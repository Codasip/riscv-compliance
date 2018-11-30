## Codasip Compliance Framework

This is a fork of RISC-V Compliance Task Group repository implementing Codasip Compliance Framework. The repository maintainers are:
- Milan Skala (milan.skala@codasip.com)
- Radek Hajek (radek.hajek@codasip.com)

## Feedback
 
If you have comments on this document or framework, please send an e-mail to rvcompliance@codasip.com.

## Contribution process

You are encouraged to contribute to this repository by submitting pull requests and by commenting on pull requests submitted by other people.

- Where a pull request is non-controversial one of the repository owners will immediately merge it. The respository uses rebase merges to maintain a linear history.

- Other pull requests will be publicised to the task group for comment and decision at a subsequent meeting of the group. Everyone is encouraged to comment on a pull request. Such pull requests will be merged by when a concensus/decision has been reached by the task group.

## Licensing

In general:
- code is licensed under the BSD 3-clause license (SPDX license identifier `BSD-3-Clause`); while
- documentation is licensed under the Creative Commons Attribution 4.0 International license (SPDX license identifier `CC-BY-4.0`).

The files [`COPYING.BSD`](./COPYING.BSD) and [`COPYING.CC`](./COPYING.CC) in the top level directory contain the complete text of these licenses.

# Overview

Compliance framework is written in Python 3 and is using Pytest framework which is a great choice for customizing the testing process. Framework is designed to be easily extended with new features, which will come with future RISC-V specification modifications. Python language has been chosen because it allows to write code fast while keeping it readable. With large Python community, there is almost everything already implemented.

Main features of the framework are:

* Easily extensible with new tests
* Support any implementation of RISC-V processor
* Automatic tests selection based on tested model configuration
* Support of custom toolchain for tests compilation
* Simple and intuitive user interface
* HTML reports for people and XML for machines
* System independent (Linux and Windows systems)

Compliance framework is a plugin-based framework, which means that integration of RISC-V model into framework is done via plugin. This brings the advantage of portability and templating. Once a plugin is written it can be moved to any other computer and can be reused there without any modifications. To minimize user's effort while integrating his model into framework, a plugin generator is implemented. The basic scheme of framework is shown in the picture below.

Each plugin consists of three components:

* **Compiler wrapper** - Object which is responsible for source compilation into format which can be later simulated on tested RISC-V model. Framework implements RISCV GCC-compatible compiler wrapper and it is used as a default, but custom compiler wrappers (for custom toolchains) are supported as well.
* **Abstract model** - Object describing model configuration and is responsible for correct simulation process.
* **Environment** - Set of header files, linker scripts and other files which are needed for correct source compilation.

<img src="docs/source/img/scheme.png" width="800" height="460"/>

When compliance framework is executed, the following steps are performed:

1. Framework loads the user plugin and configures the abstract model instance
2. Framework searches for all available compliance tests from `compliance_tests` directory
3. Framework matches tests' requirements and model properties (configuration) and generates tests which are expected to pass on given RISC-V model
4. Framework compiles test for both reference and user models (compilation may be different for each model), then simulates it on reference and user models
5. When simulation is over, abstract model implementation is responsible for signature extraction from user model
6. Framework compares signatures from reference and user model
7. When all tests are finished, framework generates HTML and XML reports and prints the summary to terminal giving the user information if his model is or is not RISC-V compliant

# Setup

Compliance framework prerequisites are:

* [x] Python 3.6+
* [x] Pytest
* [x] pytest-html
* [x] RISC-V toolchain + Spike
* [x] RISCV environmental variable set to RISC-V toolchain path

Detecting installed python version can be done with running:

`$ python --version`

Make sure that version 3.6.x or higher is installed. Python comes with tool for installing Python packages. Now, depending on how you have installed Python, it can be executed in two possible ways:

1. `$ pip install <package-name>` if `pip` is in system path 
2. `$ python -m pip install <package-name>` if `pip` is not in system path or you want to be sure that package is installed for the right Python version

The following text assumes that you have valid Python and pip in your system path.

Required prerequisites for Compliance framework execution:

`$ pip install pytest pytest-html pytest-xdist Pillow`

Plugin generator in graphical mode uses Tkinter library, which cannot be installed via pip, but should be available in distribution repositories.

For Debian-like systems:

`$ sudo apt-get install python3-tk`

For Centos-like systems:

`$ sudo yum install python3-tkinter` or `$ sudo yum install python36u-tkinter` 

For Windows systems:

* Tkinter is installed when installing Python (if Tcl/Tk has not been disabled during installation)

Compliance framework requires RISC-V Toolchain and reference model Spike. If these tools are not already built on your computer, please view ``https://github.com/riscv/riscv-tools`` and build them as described in the repository. If you have these tools built earlier, make sure that environmental variable ``$RISCV`` points to the installation directory, where tools are built.

# Usage

Compliance framework provides single entry-point script named ``rvtest.py``. Use ``--help`` argument to view all available arguments. Note that Compliance framework help containg Pytest arguments as well. To view arguments specific for Compliance framework, search for help section named **RV Compliance**.

There are some mandatory arguments which are required for Compliance framework execution:

* ``--model`` - Path to executable of user model or an file (executable/script/...) which provides interface to the model. 
* ``--plugin`` - Path to plugin containing configuration specification and behaviour definition 

# Plugin generator

Compliance framework implements plugin generator, which automatically generates plugin for model with user-defined configuration. It supports both graphical and text mode. For running the graphical Tkinter library is required (see **Setup** section). Plugin generator is implemented as a wizard (using next, next, next...).

To run plugin generator in gui mode use:

``python rvtest.py --generator --gui``

<img src="docs/source/img/gui.png" width="800" height="637"/>


# Plugin structure

Compliance framework plugin has the following directory structure:

* ``environment``
	* ``include``
		* \<header_file1\>
		* \<header_file2\>
		* ...
		* \<header_filex\>
* ``__init__.py`` - Creates a package from plugin, so it can be imported and used (may remain empty).
* ``compiler.py`` - Contains compiler wrapper implementation.
* ``rvtest_plugin.py`` - Contains model configuration, behaviour and specifies how each component is loaded.

# Integrating custom RISC-V model into framework

### Step 1: Generate plugin with Plugin generator

Using Plugin generator, specify the configuration of your processor, which you want to test and generate plugin to desired destination.
If you used any predefined target (any but `default`), you can skip step 2.

### Step 2: Implement model wrapper behaviour

Plugin contains generic implementation of the wrapper in ``rvtest_plugin.py`` file, whose class is named ``RISCVComplianceModel``. The method ``run`` implementing model execution must correspond to the tested model. All you need to do is to set arguments for the tested model, simulate application and extract it's signature. 

Method ``run`` has two arguments:
	* ``file`` - Executable application, which is going to be simulated
	* ``metadata`` - Dictionary containing metadata about current test.

``RISCVComplianceModel`` has access to model configuration you have specified while generating plugin, so you can parametrize the simulation according the model configuration. This lets you to reuse single implementation for any configuration. Configuration can be changed anytime in function ``pytest_rvtest_model_init`` which is also defined in ``rvtest_plugin.py``.

### Step 3: Execute Compliance framework

The last step is to execute framework itself. The minimal set of arguments for successful execution is:

``python rvtest.py --plugin <path_to_plugin> --model <path_to_model>``

To view all available arguments, use ``--help`` argument. Note that Compliance framework help contains Pytest arguments as well. To view arguments specific for Compliance framework, search for help section named **RV Compliance**.

# Supported targets

Plugin generator supports predefined plugins for specific targets. Currently supported targets are:

* riscvOVPsim - Imperas OVP simulator
* codasip_proprietary_SDK - Codasip SDK + Codasip simulator
* codasip_GCC - Codasip simulator + RISC-V GCC
* ri5cy_verilator - RI5CY core + verilator
* default - default empty implementation

For any other target you have to implement method for model simulation using default implementation.
