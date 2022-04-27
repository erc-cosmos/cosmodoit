"""Installation script for music_features/COSMOS_Analysis."""
import os
import shutil

import cmake_build_extension
from setuptools import setup

ext_module = cmake_build_extension.CMakeExtension(
    name="alignment",
    source_dir=os.path.join(os.path.dirname(__file__), "redist", "AlignmentTool", "Code"),
    cmake_configure_options=[f"-DCMAKE_MAKE_PROGRAM={shutil.which('ninja')}"])  # Avoids cache issues with tmp build env
# name="Pybind11Bindings",
# # Name of the resulting package name (import mymath_pybind11)
# install_prefix="mymath_pybind11",
# # Note: pybind11 is a build-system requirement specified in pyproject.toml,
# #       therefore pypa/pip or pypa/build will install it in the virtual
# #       environment created in /tmp during packaging.
# #       This cmake_depends_on option adds the pybind11 installation path
# #       to CMAKE_PREFIX_PATH so that the example finds the pybind11 targets
# #       even if it is not installed in the system.
# cmake_depends_on=["pybind11"],
# # Exposes the binary print_answer to the environment.
# # It requires also adding a new entry point in setup.cfg.
# expose_binaries=["bin/print_answer"],
# # Writes the content to the top-level __init__.py
# write_top_level_init=init_py,
# # Selects the folder where the main CMakeLists.txt is stored
# # (it could be a subfolder)
# source_dir=str(Path(__file__).parent.absolute()),
# cmake_configure_options=[
#     # This option points CMake to the right Python interpreter, and helps
#     # the logic of FindPython3.cmake to find the active version
#     f"-DPython3_ROOT_DIR={Path(sys.prefix)}",
#     "-DCALL_FROM_SETUP_PY:BOOL=ON",
#     "-DBUILD_SHARED_LIBS:BOOL=OFF",
#     # Select the bindings implementation
#     "-DEXAMPLE_WITH_SWIG:BOOL=OFF",
#     "-DEXAMPLE_WITH_PYBIND11:BOOL=ON",
# ]
# + CIBW_CMAKE_OPTIONS,
# )

setup(
    # add an extension module named 'python_cpp_example' to the package
    # 'python_cpp_example'
    ext_modules=[ext_module],
    # add custom build_ext command
    cmdclass=dict(build_ext=cmake_build_extension.BuildExtension),
)
