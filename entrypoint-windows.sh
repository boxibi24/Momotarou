#!/bin/bash

# Fail on errors.
set -e

# Make sure .bashrc is sourced
. /root/.bashrc

# Allow the workdir to be set using an env var.
# Useful for CI pipiles which use docker for their build steps
# and don't allow that much flexibility to mount volumes
#WORKDIR=${SRCDIR:-/src}

#
# In case the user specified a custom URL for PYPI, then use
# that one, instead of the default one.
#
if [[ "$PYPI_URL" != "https://pypi.python.org/" ]] || \
   [[ "$PYPI_INDEX_URL" != "https://pypi.python.org/simple" ]]; then
    # the funky looking regexp just extracts the hostname, excluding port
    # to be used as a trusted-host.
    mkdir -p /wine/drive_c/users/root/pip
    echo "[global]" > /wine/drive_c/users/root/pip/pip.ini
    echo "index = $PYPI_URL" >> /wine/drive_c/users/root/pip/pip.ini
    echo "index-url = $PYPI_INDEX_URL" >> /wine/drive_c/users/root/pip/pip.ini
    echo "trusted-host = $(echo $PYPI_URL | perl -pe 's|^.*?://(.*?)(:.*?)?/.*$|$1|')" >> /wine/drive_c/users/root/pip/pip.ini

    echo "Using custom pip.ini: "
    cat /wine/drive_c/users/root/pip/pip.ini
fi

#cd $WORKDIR


if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi # [ -f requirements.txt ]

echo "$@"

cd src

if [[ "$@" == "" ]]; then
    pyinstaller --clean -y --dist ./dist --workpath /tmp NodeEditor.spec
    pyinstaller --clean -y --dist ./dist --workpath /tmp ToolsViewer.spec
    chown -R --reference=. ./dist
else
    sh -c "$@"
fi # [[ "$@" == "" ]]

cp -r nodes ./dist/NodeEditor
cp -r ../examples ./dist/NodeEditor
cp -r nodes ./dist/ToolsViewer
cp -r ../examples ./dist/ToolsViewer

cd WixMSIPackageProject

wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh
chmod +x ./dotnet-install.sh
./dotnet-install.sh --version latest
export DOTNET_ROOT=$HOME/.dotnet
export PATH=$PATH:$DOTNET_ROOT:$DOTNET_ROOT/tools
dotnet tool install --global wix --version 4.0.2
dotnet build ./WixMSIPackageProject.sln --runtime win-x86 --configuration Release -p:ImportByWildcardBeforeSolution=false -p:GenerateSerializationAssemblies=Off

cd ../..


