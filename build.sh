#!/bin/bash

set -e

# Define version number
VERSION="1.0"

# Clean up old build files
echo "🧹 Cleaning up previous builds..."
rm -rf gdsync-${VERSION}
rm -f ../gdsync_${VERSION}-1_all.deb ../gdsync_${VERSION}-1_*.build* ../gdsync_${VERSION}-1_*.changes ../gdsync_${VERSION}.orig.tar.*

# Create source folder
echo "📁 Preparing source directory..."
mkdir gdsync-${VERSION}
cp -r usr debian gdsync-${VERSION}/

# Create orig tarball
echo "📦 Creating source tarball..."
tar czf gdsync_${VERSION}.orig.tar.gz gdsync-${VERSION}

# Enter source dir and build
cd gdsync-${VERSION}
echo "⚙️ Building .deb package..."
debuild -us -uc

echo "W rizz, your build is done, check the fricking .deb file in your parent folder"
