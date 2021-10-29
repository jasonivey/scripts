#!/usr/bin/env bash
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=sh

# Optional: I recommend to disable CCache if you are using it.
#export CCACHE_DISABLE=1

# Clean existing build directly if present.
# A full rebuild is preferable to have a stable output.
rm -rf build
mkdir -p build
mkdir -p scan-report

# Running CMake with scan-build
CC=/usr/local/opt/llvm/bin/clang-12 CXX=/usr/local/opt/llvm/bin/clang++ /usr/local/opt/llvm/bin/scan-build \
    --use-cc=/usr/local/opt/llvm/bin/clang-12 --use-c++=/usr/local/opt/llvm/bin/clang++ \
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -G "Unix Makefiles"

# Building with Make and scan-build
# -j is here to speed up a little the process by parallelizing it.
CC=/usr/local/opt/llvm/bin/clang-12 CXX=/usr/local/opt/llvm/bin/clang++ \
    /usr/local/opt/llvm/bin/scan-build  -v -v -v \
    -o scan-report \
    -analyze-headers \
    --keep-empty \
    --use-analyzer=/usr/local/opt/llvm/bin/clang-12 \
    --use-cc=/usr/local/opt/llvm/bin/clang-12 \
    --use-c++=/usr/local/opt/llvm/bin/clang++ \
    --exclude /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX11.3.sdk/usr/include \
    --exclude /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX11.3.sdk/usr/local/include \
    --exclude /Users/jasoni/dev/mmotd/build/_deps/backward-src \
    --exclude /Users/jasoni/dev/mmotd/build/_deps/catch2-src/include \
    --exclude /Users/jasoni/dev/mmotd/build/_deps/catch2-src/single_include \
    --exclude /Users/jasoni/dev/mmotd/build/_deps/certify-src/include \
    --exclude /Users/jasoni/dev/mmotd/build/_deps/cli11-src/include \
    --exclude /Users/jasoni/dev/mmotd/build/_deps/date-src/include \
    --exclude /Users/jasoni/dev/mmotd/build/_deps/fmt-src/include \
    --exclude /Users/jasoni/dev/mmotd/build/_deps/fort-src/lib \
    --exclude /Users/jasoni/dev/mmotd/build/_deps/json-src/include \
    --exclude /Users/jasoni/dev/mmotd/build/_deps/random-src/include \
    --exclude /Users/jasoni/dev/mmotd/build/_deps/scope_guard-src \
    --exclude /usr/local/opt/llvm/lib/clang/12.0.0/include \
    --exclude /usr/local/include \
    --exclude /usr/local/include/boost \
    --exclude /usr/local/opt/binutils/include \
    --exclude /usr/local/opt/llvm/include/c++/v1 \
    --exclude /usr/local/opt/openssl/include \
    --exclude build/_deps \
    -enable-checker core \
    -enable-checker core.uninitialized \
    -enable-checker cplusplus \
    -enable-checker deadcode \
    -enable-checker nullability \
    -enable-checker optin \
    -enable-checker optin.cplusplus \
    -enable-checker optin.osx \
    -enable-checker optin.performance \
    -enable-checker osx \
    -enable-checker osx.API \
    -enable-checker osx.MIG \
    -enable-checker osx.NumberObjectConversion \
    -enable-checker osx.OSObjectRetainCount \
    -enable-checker osx.ObjCProperty \
    -enable-checker osx.SecKeychainAPI \
    -enable-checker security \
    -enable-checker security.FloatLoopCounter \
    -enable-checker security.insecureAPI \
    -enable-checker unix \
    -enable-checker unix.API \
    -enable-checker unix.Malloc \
    -enable-checker unix.MallocSizeof \
    -enable-checker unix.MismatchedDeallocator \
    -enable-checker unix.Vfork \
    -enable-checker unix.cstring.BadSizeArg \
    -enable-checker unix.cstring.NullArg \
    -enable-checker valist \
    -enable-checker valist.CopyToSelf \
    -enable-checker valist.Uninitialized \
    -enable-checker valist.Unterminated \
    -enable-checker webkit \
    -enable-checker webkit.NoUncountedMemberChecker \
    -enable-checker webkit.RefCntblBaseVirtualDtor \
    -enable-checker webkit.UncountedLambdaCapturesChecker \
    make -C build -j8
