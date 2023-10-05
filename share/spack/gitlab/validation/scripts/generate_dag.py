import argparse
import os
import random
import string
import yaml


class Node(object):
    SPECIAL_STRLEN = 16
    SPECIAL_STRCHARS = string.ascii_letters + string.digits

    def __init__(self, id):
        self.id = f"{id}"
        self.children = []
        self.stage = -1
        self.special_string = "".join(
            random.choice(Node.SPECIAL_STRCHARS) for i in range(Node.SPECIAL_STRLEN)
        )

    def add_child(self):
        child_id = f"{self.id}-{len(self.children)}"
        child = Node(child_id)
        self.children.append(child)
        return child

    def print(self, depth=0):
        spaces = depth * 2 * " "
        print(f"{spaces}id: {self.id}, stage: {self.stage}")
        for child in self.children:
            child.print(depth + 1)

    def get_job_dict(self):
        self.job_dict = {
            "stage": f"stage-{self.stage}",
            "variables": {
                "SPACK_JOB_NAME": self.get_job_name(),
                "SPACK_JOB_SPECIAL_STRING": self.special_string,
                "SPACK_ARTIFACTS_ROOT": "/this/is/something/fake",
                "SPACK_CONCRETE_ENV_DIR": "/this/is/another/fake/thing",
                "SPACK_VERSION": "v0.19.1",
                "SPACK_CHECKOUT_VERSION": "deadbeef",
                "SPACK_REMOTE_MIRROR_URL": "s3://spack-binaries-prs/notreal/stacky",
                "SPACK_JOB_LOG_DIR": "jobs_scratch_dir/logs",
                "SPACK_JOB_REPRO_DIR": "jobs_scratch_dir/reproduction",
                "SPACK_JOB_TEST_DIR": "jobs_scratch_dir/test",
                "SPACK_LOCAL_MIRROR_DIR": "what_the_heck_is_this",
                "SPACK_PIPELINE_TYPE": "arbitrary and random",
                "SPACK_CI_STACK_NAME": "Noneoftheabove",
                "SPACK_CI_SHARED_PR_MIRROR_URL": "s3://spack-binaries-prs/shared-pr-mirror",
                "SPACK_REBUILD_CHECK_UP_TO_DATE": "surewhynot",
                "SPACK_REBUILD_EVERYTHING": "askmeificare",
                "KUBERNETES_CPU_REQUEST": "500m",
                "KUBERNETES_MEMORY_REQUEST": "500M",
            },
            "script": [
                "echo Hello! My job name is ${SPACK_JOB_NAME}",
                "echo     special string: ${SPACK_JOB_SPECIAL_STRING}",
            ],
            "tags": ["spack", "aws", "public", "aarch64"],
            "image": {"name": "ghcr.io/spack/e4s-amazonlinux-2:v2023-03-09", "entrypoint": [""]},
            "needs": [f"{child.get_job_name()}" for child in self.children],
            "retry": {"max": 2, "when": "always"},
            "interruptible": True,
        }
        return self.job_dict

    def get_job_name(self):
        return f"job_{self.id}"

    def count(self):
        sum = 1

        for child in self.children:
            sum += child.count()

        return sum

    def assign_stages(self):
        if len(self.children) == 0:
            self.stage = 0
            return

        for child in self.children:
            child.assign_stages()

        self.stage = self.children[0].stage + 1

    def generate_jobs(self, jobs_dict):
        for child in self.children:
            jobs_dict[child.get_job_name()] = child.generate_jobs(jobs_dict)

        return self.get_job_dict()


def build_graph(root_node, desired_depth, num_children):
    if desired_depth == 0:
        return

    for i in range(num_children):
        child = root_node.add_child()
        build_graph(child, desired_depth - 1, num_children)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="generate_dag",
        description="Generate arbitrarily large perfect k-ary tree and turn it into a .gitlab-ci.yml file",
    )

    parser.add_argument(
        "--depth", type=int, default=2, help="How many steps to get from root to leaf"
    )
    parser.add_argument(
        "--children", type=int, default=2, help="How many children does each node have"
    )
    parser.add_argument(
        "--strlen", type=int, default=16, help="Length of random string var (per job)"
    )
    parser.add_argument("--output", type=str, default=".gitlab-ci.yml", help="Path to output file")

    args = parser.parse_args()

    Node.SPECIAL_STRLEN = args.strlen
    root_node = Node("0")
    build_graph(root_node, args.depth, args.children)
    root_node.assign_stages()
    jobs = {}
    jobs[root_node.get_job_name()] = root_node.generate_jobs(jobs)
    jobs["stages"] = [f"stage-{i}" for i in range(args.depth + 1)]

    artifact_root = os.path.dirname(args.output)
    if not os.path.exists(artifact_root):
        os.makedirs(artifact_root)

    with open(args.output, "w") as fd:
        fd.write(yaml.dump(jobs))

    print(f"total number of jobs: {root_node.count()}")
    print(f"size of generated yaml on disk: {os.path.getsize(args.output)}")
