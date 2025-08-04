from os import environ
from os.path import dirname, abspath, join, isdir
from random import randint

from cocotb import test, start_soon
from cocotb.clock import Clock
from cocotb.triggers import Timer, RisingEdge
from bitstring import Bits

ROOT = dirname(
    abspath(__file__)
)

async def clear_stack(length, stack, dut, i, f):
    dut.reset.value = 1
    await RisingEdge(dut.clock)
    dut.io_in.value = 0
    await RisingEdge(dut.clock)
    await RisingEdge(dut.clock)
    await RisingEdge(dut.clock)
    stack.clear()
    assert dut.io_out.value == 0
    assert dut.io_underflow.value == 0
    assert dut.io_overflow.value == 0
    assert dut.io_isEmpty.value == int(not stack)
    assert dut.io_isFull.value == int(len(stack) == length)
    assert dut.io_popped.value == 0
    assert dut.io_peeked.value == 0
    f.write(
        ' | '.join((
            f'Cycle: {i}',
            f'Instruction: {0}',
            f'Stack: {stack}',
            '\n'
        ))
    )

async def push_to_stack(data_width, length, stack, dut, i, f):
    push_val = randint(0, 2 ** (data_width if data_width < 32 else 25) - 1)
    inst = Bits(b32 = f'{push_val:025b}0100111')
    dut.io_in.value = inst.u
    dut.reset.value = 0
    await RisingEdge(dut.clock)
    assert dut.io_out.value == 0
    assert dut.io_underflow.value == 0
    assert dut.io_popped.value == 0
    assert dut.io_peeked.value == 0
    if len(stack) < length:
        stack.append(push_val)
        assert dut.io_overflow.value == 0
    else:
        assert dut.io_overflow.value == 1
    assert dut.io_isEmpty.value == int(not stack)
    assert dut.io_isFull.value == int(len(stack) == length)
    f.write(
        ' | '.join((
            f'Cycle: {i}',
            f'Instruction: {0}',
            f'Stack: {stack}',
            '\n'
        ))
    )

async def pop_from_stack(data_width, length, stack, dut, i, f):
    pop_val = 0
    inst = Bits(b32 = f'{"0" * 25}1000011')
    dut.io_in.value = inst.u
    dut.reset.value = 0
    await RisingEdge(dut.clock)
    assert dut.io_overflow.value == 0
    assert dut.io_peeked.value == 0
    if stack:
        pop_val = stack.pop()
        assert dut.io_underflow.value == 0
        assert dut.io_popped.value == 1
    else:
        assert dut.io_underflow.value == 1
        assert dut.io_popped.value == 0
    assert dut.io_out.value == pop_val
    assert dut.io_isEmpty.value == int(not stack)
    assert dut.io_isFull.value == int(len(stack) == length)
    f.write(
        ' | '.join((
            f'Cycle: {i}',
            f'Instruction: {0}',
            f'Stack: {stack}',
            '\n'
        ))
    )

async def peek_at_stack(data_width, length, stack, dut, i, f):
    peek_val = 0
    inst = Bits(b32 = f'{"0" * 25}1{"0" * 6}')
    dut.io_in.value = inst.u
    dut.reset.value = 0
    await RisingEdge(dut.clock)
    assert dut.io_overflow.value == 0
    assert dut.io_popped.value == 0
    if stack:
        peek_val = stack[-1]
        assert dut.io_underflow.value == 0
        assert dut.io_peeked.value == 1
    else:
        assert dut.io_underflow.value == 1
        assert dut.io_peeked.value == 0
    assert dut.io_out.value == peek_val
    assert dut.io_isEmpty.value == int(not stack)
    assert dut.io_isFull.value == int(len(stack) == length)
    f.write(
        ' | '.join((
            f'Cycle: {i}',
            f'Instruction: {0}',
            f'Stack: {stack}',
            '\n'
        ))
    )

@test()
async def stack_tb(dut):
    start_soon(Clock(
        dut.clock, 1,
        units = 'ns'
    ).start(start_high = False))
    data_width = int(environ['DATA_WIDTH'])
    length = int(environ['LENGTH'])
    stack = []
    with open(
        join(ROOT, 'out', 'stack.SVGen', 'ref.log'),
        'a'
    ) as f:
        for i in range(1_000):
            instID = randint(0, 3)
            if instID == 0:
                await clear_stack(length, stack, dut, i, f)
            elif instID == 1:
                await push_to_stack(data_width, length, stack, dut, i, f)
            elif instID == 2:
                await pop_from_stack(data_width, length, stack, dut, i, f)
            elif instID == 3:
                await peek_at_stack(data_width, length, stack, dut, i, f)
