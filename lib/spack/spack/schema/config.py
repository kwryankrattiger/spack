# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
"""Schema for config.yaml configuration file.

.. literalinclude:: _spack_root/lib/spack/spack/schema/config.py
   :lines: 13-
"""

from llnl.util.lang import union_dicts

import spack.schema.projections

#: Properties for inclusion in other schemas
properties = {
    "config": {
        "type": "object",
        "default": {},
        "properties": {
            "flags": {
                "type": "object",
                "properties": {
                    "keep_werror": {"type": "string", "enum": ["all", "specific", "none"]}
                },
            },
            "shared_linking": {
                "anyOf": [
                    {"type": "string", "enum": ["rpath", "runpath"]},
                    {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["rpath", "runpath"]},
                            "bind": {"type": "boolean"},
                        },
                    },
                ]
            },
            "install_tree": {
                "anyOf": [
                    {
                        "type": "object",
                        "properties": union_dicts(
                            {"root": {"type": "string"}},
                            {
                                "padded_length": {
                                    "oneOf": [
                                        {"type": "integer", "minimum": 0},
                                        {"type": "boolean"},
                                    ]
                                }
                            },
                            spack.schema.projections.properties,
                        ),
                    },
                    {"type": "string"},  # deprecated
                ]
            },
            "install_hash_length": {"type": "integer", "minimum": 1},
            "install_path_scheme": {"type": "string"},  # deprecated
            "build_stage": {
                "oneOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]
            },
            "stage_name": {"type": "string"},
            "test_stage": {"type": "string"},
            "extensions": {"type": "array", "items": {"type": "string"}},
            "template_dirs": {"type": "array", "items": {"type": "string"}},
            "license_dir": {"type": "string"},
            "source_cache": {"type": "string"},
            "misc_cache": {"type": "string"},
            "environments_root": {"type": "string"},
            "connect_timeout": {"type": "integer", "minimum": 0},
            "verify_ssl": {"type": "boolean"},
            "suppress_gpg_warnings": {"type": "boolean"},
            "install_missing_compilers": {"type": "boolean"},
            "debug": {"type": "boolean"},
            "checksum": {"type": "boolean"},
            "deprecated": {"type": "boolean"},
            "locks": {"type": "boolean"},
            "dirty": {"type": "boolean"},
            "build_language": {"type": "string"},
            "build_jobs": {"type": "integer", "minimum": 1},
            "ccache": {"type": "boolean"},
            "compiler_launcher": {
                "oneOf": [
                    {"type": "string"},
                    {
                        "type": "object",
                        "properties": {
                            "cc": {"type": "string"},
                            "cxx": {"type": "string"},
                            "fortran": {"type": "string"},
                            "rustc": {"type": "string"},
                        },
                    },
                ]
            },
            "concretizer": {"type": "string", "enum": ["original", "clingo"]},
            "db_lock_timeout": {"type": "integer", "minimum": 1},
            "package_lock_timeout": {
                "anyOf": [{"type": "integer", "minimum": 1}, {"type": "null"}]
            },
            "allow_sgid": {"type": "boolean"},
            "install_status": {"type": "boolean"},
            "binary_index_root": {"type": "string"},
            "url_fetch_method": {"type": "string", "enum": ["urllib", "curl"]},
            "additional_external_search_paths": {"type": "array", "items": {"type": "string"}},
            "binary_index_ttl": {"type": "integer", "minimum": 0},
            "aliases": {"type": "object", "patternProperties": {r"\w[\w-]*": {"type": "string"}}},
        },
        "deprecatedProperties": {
            "properties": ["terminal_title"],
            "message": "config:terminal_title has been replaced by "
            "install_status and is ignored",
            "error": False,
        },
    }
}


#: Full schema with metadata
schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Spack core configuration file schema",
    "type": "object",
    "additionalProperties": False,
    "properties": properties,
}


def update(data):
    """Update the data in place to remove deprecated properties.

    Args:
        data (dict): dictionary to be updated

    Returns:
        True if data was changed, False otherwise
    """
    import llnl.util.tty as tty

    # currently deprecated properties are
    # install_tree: <string>
    # install_path_scheme: <string>
    # updated: install_tree: {root: <string>,
    #                         projections: <projections_dict}
    # root replaces install_tree, projections replace install_path_scheme
    changed = False

    install_tree = data.get("install_tree", None)
    if isinstance(install_tree, str):
        # deprecated short-form install tree
        # add value as `root` in updated install_tree
        data["install_tree"] = {"root": install_tree}
        changed = True

    install_path_scheme = data.pop("install_path_scheme", None)
    if install_path_scheme:
        projections_data = {"projections": {"all": install_path_scheme}}

        # update projections with install_scheme
        # whether install_tree was updated or not
        # we merge the yaml to ensure we don't invalidate other projections
        update_data = data.get("install_tree", {})
        update_data = spack.config.merge_yaml(update_data, projections_data)
        data["install_tree"] = update_data
        changed = True

    use_ccache = data.pop("ccache", None)
    if use_ccache:
        if not data.get("compiler_launcher", None):
            data["compiler_launcher"] = {"cxx": "ccache", "cc": "ccache"}
            tty.warning(
                "'config:ccache' is deprecated, use 'config:compiler_launcher:ccache' instead"
            )
            changed = True
        else:
            tty.warning("'config:ccache' is ignored, using 'config:compiler_launcher' instead")

    compiler_launcher = data.get("compiler_launcher", None)
    if isinstance(compiler_launcher, str):
        # only auto-expand launcher to C and CXX
        # Fortran and RustC both have additional
        # restrictions that need to be resolved
        # by the configuration.
        data["compiler_launcher"] = {"cxx": compiler_launcher, "cc": compiler_launcher}
        changed = True

    use_curl = data.pop("use_curl", None)
    if use_curl is not None:
        data["url_fetch_method"] = "curl" if use_curl else "urllib"
        changed = True

    shared_linking = data.get("shared_linking", None)
    if isinstance(shared_linking, str):
        # deprecated short-form shared_linking: rpath/runpath
        # add value as `type` in updated shared_linking
        data["shared_linking"] = {"type": shared_linking, "bind": False}
        changed = True

    return changed
