# Install Python 3.11 for ArcGIS Compatibility

## Why Python 3.11?

From the error message, we can see that ArcGIS API versions have these Python requirements:
- Latest versions (2.4.x): `Requires-Python <3.13,>=3.10`
- Older versions (2.3.x): `Requires-Python <3.12,>=3.9`
- Version 1.9.1 (Azure Functions): `Requires-Python <3.10,>=3.7`

**Python 3.11 is the sweet spot** - it's compatible with all ArcGIS API versions including the latest ones.

## Option 1: Install Python 3.11 System-Wide

### Download and Install
1. Go to https://www.python.org/downloads/
2. Download **Python 3.11.9** (latest 3.11 version)
3. Run the installer
4. **Important**: Check "Add Python to PATH" during installation
5. Choose "Install for all users" if you want system-wide access

### Verify Installation
```bash
# Check if Python 3.11 is installed
python --version
# Should show: Python 3.11.x

# Or if you have multiple Python versions
py -3.11 --version
```

## Option 2: Use pyenv (Recommended for Multiple Python Versions)

### Install pyenv-win
```bash
# Install pyenv-win via git
git clone https://github.com/pyenv-win/pyenv-win.git %USERPROFILE%\.pyenv

# Add to PATH (add these to your environment variables)
%USERPROFILE%\.pyenv\pyenv-win\bin
%USERPROFILE%\.pyenv\pyenv-win\shims
```

### Install Python 3.11 with pyenv
```bash
# List available versions
pyenv install --list | findstr 3.11

# Install Python 3.11.9
pyenv install 3.11.9

# Set as global default
pyenv global 3.11.9

# Verify
python --version
```

## Option 3: Use conda/miniconda (Alternative)

### Install miniconda
1. Download from https://docs.anaconda.com/miniconda/
2. Install miniconda
3. Create Python 3.11 environment:

```bash
# Create environment with Python 3.11
conda create -n arcgis-env python=3.11

# Activate environment
conda activate arcgis-env

# Verify
python --version
```

## Next Steps

Once you have Python 3.11 installed, we'll create a new setup script that uses it specifically.

Choose the option that works best for your setup, and let me know when Python 3.11 is ready!