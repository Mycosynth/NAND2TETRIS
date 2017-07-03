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

def main(file_or_dir):
  #os.chdir('/Users/nate/Desktop/nand2tetris/projects/07')
  if os.path.isdir(file_or_dir):
    codeWriter_1 = codeWriter(file_or_dir)
    for root, dirs, files in os.walk(file_or_dir):
      for file in files:
        if file.endswith('.vm'):
          the_parser = parser(file_to_arr(file))
          process_1_parser(the_parser,codeWriter_1)
    codeWriter_1.writeToFile()
  elif os.path.isfile(file_or_dir):
    parser_1 = parser(file_to_arr(file_or_dir))
    codeWriter_1 = codeWriter(file_or_dir)
    process_1_parser(parser_1,codeWriter_1)
    codeWriter_1.writeToFile()
  else:
    print('error input is neither file or dir, in main line 9')

def process_1_parser(the_parser,the_writer):
  while the_parser.hasMoreCommands():
    the_parser.advance()
    op = the_parser.commandType()
    if op == C_ARITHMETIC:
      the_writer.writeArithmetic(the_parser.arg1())
    elif (op == C_PUSH) or (op == C_POP):
      the_writer.writePushPop(op,the_parser.arg1(),the_parser.arg2())
    
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
    return command_type_dict[working_line.partition(' ')[0]]  
  
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
    
  def writeToFile(self):
    self.file.write(self.cur_asm)
    self.file.close()
    
  def writeArithmetic(self,command_string):
    if command_string in ['add','sub','and','or']:
      self.cur_asm += self.x_op_y(command_string)
    elif command_string in ['neg','not']:
      self.cur_asm += self.op_x(command_string)
    elif command_string in ['eq','lt','gt']:
      self.cur_asm += self.x_bool_y(command_string)
  
  def goto_label(self,label,if_goto):
    jump_type = 'JMP'
    if if_goto:
      jump_type = 'JNE'
    if not label in label_dict:
      label_dict[label] = self.uniqify_label(label)
    cur_label = label_dict[label]
    return self.d_equal_sp_minus_1_reg+'@'+cur_label+'\nD;'+jump_type
  
  def writePushPop(self,op,seg_name,index):
    asm_to_write = ''
    if op == C_PUSH:
      if seg_name == 'constant':
        asm_to_write = '@'+str(index)+'\nD=A\n@SP\nA=M\nM=D\n'+self.inc_sp_reg()
      else:
	asm_to_write = self.at_memory_segment(seg_name,index)+'D=M\n@SP\nA=M\nM=D\n'+self.inc_sp_reg()
    elif op == C_POP:
	asm_to_write = self.at_memory_segment(seg_name,index)+'D=A\n@R13\nM=D\n@SP\nA=M-1\nD=M\n@R13\nA=M\nM=D\n'+self.dec_sp_reg()
    else:
      print('Error not push/pop')
    self.cur_asm += asm_to_write
    
  def at_memory_segment(self,seg_name,index):
    if seg_name in ['local','argument','this','that']:
      cur_seg = {'local':'LCL','argument':'ARG','this':'THIS','that':'THAT'}[seg_name]
      return '@'+cur_seg+'\nD=M\n@'+str(index)+'\nA=A+D\n'
    elif seg_name in ['pointer','temp']:
      cur_offset = {'pointer':'3','temp':'5'}[seg_name]
      return '@'+cur_offset+'\nD=A\n@'+str(index)+'\nA=A+D\n'
    elif seg_name == 'static':
      return '@'+self.fileName+'.'+str(index)+'\n'
 
  
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
    main(sys.argv[1])
