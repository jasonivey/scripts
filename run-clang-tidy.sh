#!/usr/bin/env bash
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=sh

#set CLANG_TIDY_CHECKS="-*,clang-analyzer-alpha.clone.CloneChecker,clang-analyzer-alpha.core.BoolAssignment,clang-analyzer-alpha.core.C11Lock,clang-analyzer-alpha.core.CastSize,clang-analyzer-alpha.core.CastToStruct,clang-analyzer-alpha.core.Conversion,clang-analyzer-alpha.core.DynamicTypeChecker,clang-analyzer-alpha.core.FixedAddr,clang-analyzer-alpha.core.IdenticalExpr,clang-analyzer-alpha.core.PointerArithm,clang-analyzer-alpha.core.PointerSub,clang-analyzer-alpha.core.PthreadLockBase,clang-analyzer-alpha.core.SizeofPtr,clang-analyzer-alpha.core.StackAddressAsyncEscape,clang-analyzer-alpha.core.TestAfterDivZero,clang-analyzer-alpha.cplusplus.ContainerModeling,clang-analyzer-alpha.cplusplus.DeleteWithNonVirtualDtor,clang-analyzer-alpha.cplusplus.EnumCastOutOfRange,clang-analyzer-alpha.cplusplus.InvalidatedIterator,clang-analyzer-alpha.cplusplus.IteratorModeling,clang-analyzer-alpha.cplusplus.IteratorRange,clang-analyzer-alpha.cplusplus.MismatchedIterator,clang-analyzer-alpha.cplusplus.STLAlgorithmModeling,clang-analyzer-alpha.cplusplus.SmartPtr,clang-analyzer-alpha.deadcode.UnreachableCode,clang-analyzer-alpha.fuchsia.Lock,clang-analyzer-alpha.llvm.Conventions,clang-analyzer-alpha.nondeterminism.PointerIteration,clang-analyzer-alpha.nondeterminism.PointerSorting,clang-analyzer-alpha.osx.cocoa.DirectIvarAssignment,clang-analyzer-alpha.osx.cocoa.InstanceVariableInvalidation,clang-analyzer-alpha.osx.cocoa.IvarInvalidationModeling,clang-analyzer-alpha.osx.cocoa.MissingInvalidationMethod,clang-analyzer-alpha.osx.cocoa.localizability.PluralMisuseChecker,clang-analyzer-alpha.security.ArrayBound,clang-analyzer-alpha.security.ArrayBoundV2,clang-analyzer-alpha.security.MallocOverflow,clang-analyzer-alpha.security.MmapWriteExec,clang-analyzer-alpha.security.ReturnPtrRange,clang-analyzer-alpha.security.cert.pos.34c,clang-analyzer-alpha.security.taint.TaintPropagation,clang-analyzer-alpha.unix.BlockInCriticalSection,clang-analyzer-alpha.unix.Chroot,clang-analyzer-alpha.unix.PthreadLock,clang-analyzer-alpha.unix.SimpleStream,clang-analyzer-alpha.unix.StdCLibraryFunctionArgs,clang-analyzer-alpha.unix.Stream,clang-analyzer-alpha.unix.cstring.BufferOverlap,clang-analyzer-alpha.unix.cstring.NotNullTerminated,clang-analyzer-alpha.unix.cstring.OutOfBounds,clang-analyzer-alpha.webkit.UncountedCallArgsChecker,clang-analyzer-alpha.webkit.UncountedLocalVarsChecker,clang-analyzer-apiModeling.StdCLibraryFunctions,clang-analyzer-apiModeling.TrustNonnull,clang-analyzer-apiModeling.google.GTest,clang-analyzer-apiModeling.llvm.CastValue,clang-analyzer-apiModeling.llvm.ReturnValue,clang-analyzer-core.CallAndMessage,clang-analyzer-core.CallAndMessageModeling,clang-analyzer-core.DivideZero,clang-analyzer-core.DynamicTypePropagation,clang-analyzer-core.NonNullParamChecker,clang-analyzer-core.NonnilStringConstants,clang-analyzer-core.NullDereference,clang-analyzer-core.StackAddrEscapeBase,clang-analyzer-core.StackAddressEscape,clang-analyzer-core.UndefinedBinaryOperatorResult,clang-analyzer-core.VLASize,clang-analyzer-core.builtin.BuiltinFunctions,clang-analyzer-core.builtin.NoReturnFunctions,clang-analyzer-core.uninitialized.ArraySubscript,clang-analyzer-core.uninitialized.Assign,clang-analyzer-core.uninitialized.Branch,clang-analyzer-core.uninitialized.CapturedBlockVariable,clang-analyzer-core.uninitialized.UndefReturn,clang-analyzer-cplusplus.InnerPointer,clang-analyzer-cplusplus.Move,clang-analyzer-cplusplus.NewDelete,clang-analyzer-cplusplus.NewDeleteLeaks,clang-analyzer-cplusplus.PlacementNew,clang-analyzer-cplusplus.PureVirtualCall,clang-analyzer-cplusplus.SelfAssignment,clang-analyzer-cplusplus.SmartPtrModeling,clang-analyzer-cplusplus.VirtualCallModeling,clang-analyzer-deadcode.DeadStores,clang-analyzer-fuchsia.HandleChecker,clang-analyzer-nullability.NullPassedToNonnull,clang-analyzer-nullability.NullReturnedFromNonnull,clang-analyzer-nullability.NullabilityBase,clang-analyzer-nullability.NullableDereferenced,clang-analyzer-nullability.NullablePassedToNonnull,clang-analyzer-nullability.NullableReturnedFromNonnull,clang-analyzer-optin.cplusplus.UninitializedObject,clang-analyzer-optin.cplusplus.VirtualCall,clang-analyzer-optin.mpi.MPI-Checker,clang-analyzer-optin.osx.OSObjectCStyleCast,clang-analyzer-optin.osx.cocoa.localizability.EmptyLocalizationContextChecker,clang-analyzer-optin.osx.cocoa.localizability.NonLocalizedStringChecker,clang-analyzer-optin.performance.GCDAntipattern,clang-analyzer-optin.performance.Padding,clang-analyzer-optin.portability.UnixAPI,clang-analyzer-osx.API,clang-analyzer-osx.MIG,clang-analyzer-osx.NSOrCFErrorDerefChecker,clang-analyzer-osx.NumberObjectConversion,clang-analyzer-osx.OSObjectRetainCount,clang-analyzer-osx.ObjCProperty,clang-analyzer-osx.SecKeychainAPI,clang-analyzer-osx.cocoa.AtSync,clang-analyzer-osx.cocoa.AutoreleaseWrite,clang-analyzer-osx.cocoa.ClassRelease,clang-analyzer-osx.cocoa.Dealloc,clang-analyzer-osx.cocoa.IncompatibleMethodTypes,clang-analyzer-osx.cocoa.Loops,clang-analyzer-osx.cocoa.MissingSuperCall,clang-analyzer-osx.cocoa.NSAutoreleasePool,clang-analyzer-osx.cocoa.NSError,clang-analyzer-osx.cocoa.NilArg,clang-analyzer-osx.cocoa.NonNilReturnValue,clang-analyzer-osx.cocoa.ObjCGenerics,clang-analyzer-osx.cocoa.RetainCount,clang-analyzer-osx.cocoa.RetainCountBase,clang-analyzer-osx.cocoa.RunLoopAutoreleaseLeak,clang-analyzer-osx.cocoa.SelfInit,clang-analyzer-osx.cocoa.SuperDealloc,clang-analyzer-osx.cocoa.UnusedIvars,clang-analyzer-osx.cocoa.VariadicMethodTypes,clang-analyzer-osx.coreFoundation.CFError,clang-analyzer-osx.coreFoundation.CFNumber,clang-analyzer-osx.coreFoundation.CFRetainRelease,clang-analyzer-osx.coreFoundation.containers.OutOfBounds,clang-analyzer-osx.coreFoundation.containers.PointerSizedValues,clang-analyzer-security.FloatLoopCounter,clang-analyzer-security.insecureAPI.DeprecatedOrUnsafeBufferHandling,clang-analyzer-security.insecureAPI.SecuritySyntaxChecker,clang-analyzer-security.insecureAPI.UncheckedReturn,clang-analyzer-security.insecureAPI.bcmp,clang-analyzer-security.insecureAPI.bcopy,clang-analyzer-security.insecureAPI.bzero,clang-analyzer-security.insecureAPI.decodeValueOfObjCType,clang-analyzer-security.insecureAPI.getpw,clang-analyzer-security.insecureAPI.gets,clang-analyzer-security.insecureAPI.mkstemp,clang-analyzer-security.insecureAPI.mktemp,clang-analyzer-security.insecureAPI.rand,clang-analyzer-security.insecureAPI.strcpy,clang-analyzer-security.insecureAPI.vfork,clang-analyzer-unix.API,clang-analyzer-unix.DynamicMemoryModeling,clang-analyzer-unix.Malloc,clang-analyzer-unix.MallocSizeof,clang-analyzer-unix.MismatchedDeallocator,clang-analyzer-unix.Vfork,clang-analyzer-unix.cstring.BadSizeArg,clang-analyzer-unix.cstring.CStringModeling,clang-analyzer-unix.cstring.NullArg,clang-analyzer-valist.CopyToSelf,clang-analyzer-valist.Uninitialized,clang-analyzer-valist.Unterminated,clang-analyzer-valist.ValistBase,clang-analyzer-webkit.NoUncountedMemberChecker,clang-analyzer-webkit.RefCntblBaseVirtualDtor,clang-analyzer-webkit.UncountedLambdaCapturesChecker"

git ls-files | grep -e "^.*\.cpp$" -e "^.*\.h$" | while read filename
do
    echo "running clang tidy on $filename"
    /usr/local/opt/llvm/bin/clang-tidy --use-color --format-style=file -fix --fix-errors -p=build $filename
done

#set CLANG_TIDY_CHECKS=