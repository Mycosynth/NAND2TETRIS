import os
import sys

C_ARITHMETIC = 1
C_PUSH = 2
C_POP = 3
C_LABEL = 4
C_GOTO = 5
C_IF = 6
C_FUNCTION = 7
C_RETURN = 8
C_CALL = 9
label_dict = {}
cur_file_name = ''
file_counter = 0

def main(file_or_dir):
  global file_counter
  if os.path.isdir(file_or_dir):
    codeWriter_1 = codeWriter(file_or_dir)
    for root, dirs, files in os.walk(file_or_dir):
      for file in files:
        if file.endswith('.vm'):
          the_parser = parser(file_to_arr(root + '/' + file))
          process_1_parser(the_parser,codeWriter_1)
          file_counter += 1
    codeWriter_1.writeToFile()
  elif os.path.isfile(file_or_dir):
    parser_1 = parser(file_to_arr(file_or_dir))
    codeWriter_1 = codeWriter(file_or_dir)
    process_1_parser(parser_1,codeWriter_1)
    codeWriter_1.writeToFile()
  else:
    print('error input is neither file or dir, in main line 9')

def process_1_parser(the_parser,the_writer):
  in_function = []
  while the_parser.hasMoreCommands():
    cur_function = None
    if len(in_function) > 0:
      cur_function = in_function[-1]
    the_parser.advance()
    op = the_parser.commandType()
    if op == C_ARITHMETIC:
      the_writer.writeArithmetic(the_parser.arg1())
    elif (op == C_PUSH) or (op == C_POP):
      the_writer.writePushPop(op,the_parser.arg1(),the_parser.arg2())
    elif op == C_GOTO:
      the_writer.writeGoto(the_parser.arg1(),cur_function)
    elif op == C_IF:
      the_writer.writeIf(the_parser.arg1(),cur_function)
    elif op == C_LABEL:
      the_writer.writeLabel(the_parser.arg1(),cur_function)
    elif op == C_FUNCTION:
      in_function.append(the_parser.arg1())
      the_writer.writeFunction(the_parser.arg1(),int(the_parser.arg2()))
    elif op == C_CALL:
      the_writer.writeCall(the_parser.arg1(),int(the_parser.arg2()))
    elif op == C_RETURN:
      in_function = in_function[:-1]
      the_writer.writeReturn()

def file_to_arr(file_name):
  f = open(file_name)
  cur_file_name = file_name
  return_val = [line.rstrip('\n') for line in f]
  f.close()
  return return_val
  
class parser():
  def __init__(self,vm_file_arr):
    self.vm_arr = [line.replace('\r','') for line in vm_file_arr if (line != '\n') and (line != '\r') and (not line.strip().startswith("//"))]
    self.num_lines = len(self.vm_arr)
    self.next_line_index = 0
    label_dict = {}
    
  def hasMoreCommands(self):
    return self.next_line_index < self.num_lines
  
  def advance(self):
    self.current_line = self.vm_arr[self.next_line_index]
    self.next_line_index += 1
    while (self.current_line == '') or (self.current_line == '\n'):
        self.current_line = self.vm_arr[self.next_line_index]
        self.next_line_index += 1
  
  def commandType(self):
    working_line = self.current_line
    command_type_dict = {'add':C_ARITHMETIC,
                         'sub':C_ARITHMETIC,
                         'neg':C_ARITHMETIC,
                         'eq':C_ARITHMETIC,
                         'gt':C_ARITHMETIC,
                         'lt':C_ARITHMETIC,
                         'and':C_ARITHMETIC,
                         'not':C_ARITHMETIC,
                         'or':C_ARITHMETIC,
                         'push':C_PUSH,
                         'pop':C_POP,
                         'return':C_RETURN,
                         'goto':C_GOTO,
                         'label':C_LABEL,
                         'if-goto':C_IF,
                         'function':C_FUNCTION,
                         'call':C_CALL}
    return command_type_dict[working_line.split()[0]]  
  
  def arg1(self):
    working_line = self.current_line
    working_line = working_line.split(' ')
    if len(working_line) == 1:
      return working_line[0]
    else:
      return working_line[1]
  
  def arg2(self):
    working_line = self.current_line
    return working_line.split(' ')[2]
    
class codeWriter():
  def __init__(self,assembly_file):
    self.fileName = assembly_file.split('.')[0] + '.asm'
    self.file = open(self.fileName,'w+')
    self.unique_id = 0
    self.cur_asm = ''
    self.writeInit()
  
  def writeReturn(self):
    #FRAME = LCL , @R14 will contain FRAME
    self.cur_asm += '@LCL\nD=M\n@R14\nM=D\n'
    #RET = *(FRAME-5) , @R15 will contain RET
    self.cur_asm += '@R14\nD=M\n@5\nA=D-A\nD=M\n@R15\nM=D\n'
    #*ARG = pop()
    self.cur_asm += '@SP\nA=M-1\nD=M\n@ARG\nA=M\nM=D\n'
    #SP = ARG+1
    self.cur_asm += '@ARG\nD=M+1\n@SP\nM=D\n'
    #THAT = *(FRAME-1)
    self.cur_asm += '@R14\nD=M\n@1\nA=D-A\nD=M\n@THAT\nM=D\n'
    #THIS = *(FRAME-2)
    self.cur_asm += '@R14\nD=M\n@2\nA=D-A\nD=M\n@THIS\nM=D\n'
    #ARG = *(FRAME-3)
    self.cur_asm += '@R14\nD=M\n@3\nA=D-A\nD=M\n@ARG\nM=D\n'
    #LCL = *(FRAME-4)
    self.cur_asm += '@R14\nD=M\n@4\nA=D-A\nD=M\n@LCL\nM=D\n'
    #goto RET
    self.cur_asm += '@R15\nA=M\n0;JMP\n'
    
  def writeToFile(self):
    self.file.write(self.cur_asm)
    self.file.close()
    
  def writeFunction(self,function_name,num_args):
    self.cur_asm += '('+function_name+')\n'
    while num_args>0:
      self.writePushPop(C_PUSH,'constant',0)
      num_args -= 1
  
  #call f n, f=function_name, n=args_pushed
  def writeCall(self,function_name,args_pushed): 
    self.return_label = self.uniqify_label('return_address')
    #push return address
    self.cur_asm += '@'+self.return_label+'\nD=A\n@SP\nM=D\n'+self.inc_sp_reg()
    #push LCL
    self.writePushPop(C_PUSH,'local',0)
    #push ARG
    self.writePushPop(C_PUSH,'argument',0)
    #push THIS
    self.writePushPop(C_PUSH,'this',0)
    #push THAT
    self.writePushPop(C_PUSH,'that',0)
    #ARG = SP-n-5
    self.cur_asm += '@5\nD=A\n@'+str(args_pushed)+'\nD=D+A\n@SP\nD=M-D\n@ARG\nM=D\n'
    #LCL = SP
    self.cur_asm += '@SP\nD=M\n@LCL\nM=D\n'
    #goto f
    self.cur_asm += '@'+function_name+'\n0;JMP\n'
    #(return-address)
    self.cur_asm += '('+self.return_label+')\n'

  def writeInit(self):
    self.cur_asm += '@255\nD=A\n@SP\nM=D\n'
    #only jump if Sys.vm exists! :)
    self.writeCall('Sys.init',0)
  
  def writeArithmetic(self,command_string):
    if command_string in ['add','sub','and','or']:
      self.cur_asm += self.x_op_y(command_string)
    elif command_string in ['neg','not']:
      self.cur_asm += self.op_x(command_string)
    elif command_string in ['eq','lt','gt']:
      self.cur_asm += self.x_bool_y(command_string)

  def writeGoto(self,label,function_name):
    self.cur_asm += self.goto_label(label,False,function_name) 
  
  def writeIf(self,label,function_name):
    self.cur_asm += self.goto_label(label,True,function_name)

  def writeLabel(self,label,function_name):
    cur_label = label
    if not function_name is None:
      cur_label = function_name + '$' + cur_label
    if not cur_label in label_dict:
      label_dict[cur_label] = self.uniqify_label(cur_label)
    cur_label = label_dict[cur_label]
    self.cur_asm += '(' + cur_label + ')\n'

  def goto_label(self,label,if_goto,function_name):
    jump_type = 'JMP'
    if if_goto:
      jump_type = 'JNE'
    wrk_label = label
    if not function_name is None:
      wrk_label = function_name + '$' + label
    if not wrk_label in label_dict:
      label_dict[wrk_label] = self.uniqify_label(wrk_label)
    cur_label = label_dict[wrk_label]
    return self.d_equal_sp_minus_1_reg()+'@'+cur_label+'\nD;'+jump_type+'\n'
  
  def writePushPop(self,op,seg_name,index):
    asm_to_write = ''
    if op == C_PUSH:
      if seg_name == 'constant':
        asm_to_write = '@'+str(index)+'\nD=A\n@SP\nA=M\nM=D\n'+self.inc_sp_reg()
      else:
	asm_to_write = self.at_memory_segment(seg_name,index)+'D=M\n@SP\nA=M\nM=D\n'+self.inc_sp_reg()
    elif op == C_POP:
      if seg_name == 'static':
        asm_to_write = '@SP\nA=M-1\nD=M\n'+self.dec_sp_reg()+self.at_memory_segment(seg_name,index)+'M=D\n'
      else:
        asm_to_write = self.at_memory_segment(seg_name,index)+'D=A\n@R13\nM=D\n@SP\nA=M-1\nD=M\n@R13\nA=M\nM=D\n'+self.dec_sp_reg()
    self.cur_asm += asm_to_write
    
  def at_memory_segment(self,seg_name,index):
    if seg_name in ['local','argument','this','that']:
      cur_seg = {'local':'LCL','argument':'ARG','this':'THIS','that':'THAT'}[seg_name]
      return '@'+cur_seg+'\nD=M\n@'+str(index)+'\nA=A+D\n'
    elif seg_name in ['pointer','temp']:
      cur_offset = {'pointer':'3','temp':'5'}[seg_name]
      return '@'+cur_offset+'\nD=A\n@'+str(index)+'\nA=A+D\n'
    elif seg_name == 'static':
      return '@x'+str(file_counter)+'x'+str(index)+'\n' #book says to use the filename, that fails their tests due to excessive length,xfilecounterxstaticcounter works
 
  
  def x_op_y(self,op):
    op_dict = {'add':'+','sub':'-','and':'&','or':'|'}
    return self.d_equal_sp_minus_1_reg() + '@SP\nA=M-1\nA=A-1\nM=M'+op_dict[op]+'D\n'+self.dec_sp_reg()
    
  def op_x(self,op):
    op_dict = {'neg':'-','not':'!'}
    return '@SP\nA=M-1\nM='+op_dict[op]+'M\n'
  
  def x_bool_y(self,bool_type):
    bool_dict = {'eq':'JEQ','gt':'JGT','lt':'JLT'}
    label_1 = self.uniqify_label('bool_true')
    label_2 = self.uniqify_label('boo8l_false')
    return self.x_op_y('sub')+self.d_equal_sp_minus_1_reg()+'@'+label_1+'\nD;'+bool_dict[bool_type]+'\n@SP\nA=M-1\nM=0\n@'+label_2+'\n0;JMP\n('+label_1+')\n'+self.d_equal_sp_minus_1_reg()+'M=-1\n('+label_2+')\n'
    
  def d_equal_sp_minus_1_reg(self):
    return '@SP\nA=M-1\nD=M\n'
    
  def dec_sp_reg(self):
    return '@SP\nM=M-1\n'
    
  def inc_sp_reg(self):
    return '@SP\nM=M+1\n'
    
  def uniqify_label(self,label):
    a = self.unique_id
    self.unique_id += 1
    return label + str(a)

if __name__ == "__main__":
   # print(sys.argv[1])
   # print(os.path.isdir(sys.argv[1]))
    main(sys.argv[1])
