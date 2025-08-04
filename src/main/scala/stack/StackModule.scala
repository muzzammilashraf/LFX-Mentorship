package stack

import chisel3._
import chisel3.util._
import chisel3.stage.ChiselStage
import java.nio.file.Paths

class StackModule(val dataWidth: Int, val len: Int) extends Module {
  val io = IO(new Bundle {
    val in        = Input(UInt(32.W))             // Instruction input (opcode + immediate)
    val out       = Output(UInt(dataWidth.W))     // Top-of-stack value
    val underflow = Output(Bool())                // Underflow on pop/peek
    val overflow  = Output(Bool())                // Overflow on push
    val isEmpty   = Output(Bool())                // Stack empty?
    val isFull    = Output(Bool())                // Stack full?
    val popped    = Output(Bool())                // Successful pop
    val peeked    = Output(Bool())                // Successful peek
  })

  // Stack and stack pointer
  val stack   = RegInit(VecInit(Seq.fill(len)(0.U(dataWidth.W))))
  val sp      = RegInit(0.U(log2Ceil(len + 1).W))
  val next_sp = WireDefault(sp)

  // Instruction decoding
  val opcode = io.in(6, 0)
  val imm    = io.in(31, 7)
  val imm_padded = if (dataWidth <= 25) {
    imm(24, 0).pad(dataWidth)
  } else {
    Cat(0.U((dataWidth - 25).W), imm(24, 0))
  }

  // Default outputs
  io.out       := 0.U
  io.underflow := false.B
  io.overflow  := false.B
  io.popped    := false.B
  io.peeked    := false.B

  // Stack operation logic only when NOT in reset
  when (!reset.asBool) {
    switch(opcode) {
      is("b0100111".U) { // PUSH
        when(sp === len.U) {
          io.overflow := true.B
        } .otherwise {
          stack(sp) := imm_padded
          next_sp := sp + 1.U
        }
      }

      is("b1000011".U) { // POP
        when(sp === 0.U) {
          io.underflow := true.B
        } .otherwise {
          val new_sp = sp - 1.U
          io.out := stack(new_sp)
          io.popped := true.B
          next_sp := new_sp
        }
      }

      is("b1000000".U) { // PEEK
        when(sp === 0.U) {
          io.underflow := true.B
        } .otherwise {
          io.out := stack(sp - 1.U)
          io.peeked := true.B
        }
      }
    }
  }

  // Update stack pointer and status flags
  sp := next_sp
  io.isEmpty := next_sp === 0.U
  io.isFull  := next_sp === len.U
}

object SVGen extends App {
  val out = Paths.get(
    "out",
    this.getClass
      .getName
      .stripSuffix("$")
  ).toString
  new ChiselStage().emitSystemVerilog(
    new StackModule(args(0).toInt, args(1).toInt),
    Array("--target-dir", out),
  )
}
