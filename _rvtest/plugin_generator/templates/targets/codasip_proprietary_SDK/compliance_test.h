// RISC-V Compliance Test Header File
// Copyright (c) 2017, Codasip Ltd. All Rights Reserved.
// See LICENSE for license details.
//
// Description: Common header file for RV32I tests

#ifndef _COMPLIANCE_TEST_H
#define _COMPLIANCE_TEST_H

#include "riscv_test.h"

//-----------------------------------------------------------------------
// RV Compliance Macros
//-----------------------------------------------------------------------

#define RV_COMPLIANCE_HALT                                                    \
        add x15, x0, 1;                                                       \
        sw x15, codasip_syscall, t0;                                          \

#define RV_COMPLIANCE_RV32M                                                   \
                                                                              \

#define RV_COMPLIANCE_CODE_BEGIN                                              \
        .section .text.init;                                                  \
        .align  4;                                                            \
        .globl _start;                                                        \
        _start:                                                               \
        jal x0, _code_start;                                                  \
        unimp;                                                                \
        unimp;                                                                \
        unimp;                                                                \
        .global codasip_syscall;                                              \
        codasip_syscall:                                                      \
        _code_start:                                                          \
        .global _code_start;

#define RV_COMPLIANCE_CODE_END                                                \
                                                                              \

#define RV_COMPLIANCE_DATA_BEGIN                                              \
        .align 4;                                                             \
        .global codasip_signature_start;                                      \
        codasip_signature_start:                                              \

#define RV_COMPLIANCE_DATA_END                                                \
        .align 4;                                                             \
        .global codasip_signature_end;                                        \
        codasip_signature_end:                                                \
        .word 0;                                                              \
        .word 0;                                                              \
        .word 0;                                                              \
        .word 0;                                                              \

// define __riscv_xlen for test_macros.h
// this is not set in Codasip SDK
#ifdef CODASIP_RV64
#define __riscv_xlen    64
#else
#define __riscv_xlen    32
#endif

#endif

