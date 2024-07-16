"""
Groep project pygame door: Boudewijn van der Heide, Robin Paumen, Thijn Linssen, Lieuwe van Engelenburg, Quiten Blekman

Wij hebben onze eigen implementatie gemaakt voor een CHIP-8 virtual machine

Wij hebben de volgende code architechtuur gebruikt:

- Een Cpu class:
    De Cpu class zorgt voor de initialisatie van alle cpu componenten (denk aan de program counter, memory, regesters, etc)
    Daarnaast zijn hier de CPU-instructies gedefineerd en opgeslagen als hexadecimal values

- Een Input class:
    De Input class zorgt voor de initialisatie van alle input die de gebruiker kan geven
    Dit zijn de keyboard-inputs voor bepaalde programma's, en de input voor de ROM file (programma die de Cpu kan runnen)

- Een Display class:
    De Display class zorgt voor de initialisatie van het scherm en de font die de cpu gebruikt. 

- Een main function:
    De main functie zorgt voor de algemenen dependecy-injection en het uitvoeren van de functies van de classes

"""


import pygame
import random
import sys


class Cpu:
    def __init__(self, input_class, display_class):
        
        self.input_class = input_class
        self.display_class = display_class

        self.draw = True
        self.timer = pygame.time.Clock()

        self.memory = [0] * 4096
        self.registers = [0] * 16
        
        self.address_reg = 0

        self.last_op_code = 0
        self.op_code = 0

        self.Vy = 0
        self.Vx = 0
        self.I = 0

        self.delay_timer = 0
        self.sound_timer = 0

        self.stack = [0] * 16

        self.pc = 0x200
        self.stack_ptr = 0

        # Init opcodes/cpu instructions as hexadecimal value
        self.opfunctions = {
            0x0000: self.op_0nnn,
            0x00E0: self.op_00E0,
            0x000E: self.op_00EE,
            0x1000: self.op_1nnn,
            0x2000: self.op_2nnn,
            0x3000: self.op_3xkk,
            0x4000: self.op_4xkk,
            0x5000: self.op_5xy0,
            0x6000: self.op_6xkk,
            0x7000: self.op_7xkk,
            0x8000: self.op_8nnn,
            0x8001: self.op_8xy1,
            0x8002: self.op_8xy2,
            0x8003: self.op_8xy3,
            0x8004: self.op_8xy4,
            0x8005: self.op_8xy5,
            0x8006: self.op_8xy6,
            0x8007: self.op_8xy7,
            0x800E: self.op_8xyE,
            0x9000: self.op_9xy0,
            0xA000: self.op_Annn,
            0xB000: self.op_Bnnn,
            0xC000: self.op_Cxkk,
            0xD000: self.op_Dxyn,
            0xE000: self.op_Ennn,
            0xE00E: self.op_Ex9E,
            0xE001: self.op_ExA1,
            0xF000: self.op_Fnnn,
            0xF007: self.op_Fx07,
            0xF00A: self.op_Fx0A,
            0xF015: self.op_Fx15,
            0xF018: self.op_Fx18,
            0xF01E: self.op_Fx1E,
            0xF029: self.op_Fx29,
            0xF033: self.op_Fx33,
            0xF055: self.op_Fx55,
            0xF065: self.op_Fx65
        }
    
    def cpu_cycle(self):

        self.draw = False

        self.lastop = hex(self.op_code)

        self.op_code = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]  # opcodes 2 bytes long, combining them here
        self.currentop = hex(self.op_code)

        self.Vx = (self.op_code & 0x0f00) >> 8  # extract the 2nd nibble and shift by 8 bits
        self.Vy = (self.op_code & 0x00f0) >> 4  # extract the 3rd nibble and shift by 4 bits


        hexop = self.op_code & 0xF000
        try:
            self.opfunctions[hexop]()
        except Exception as e:
            print(f"Invalid op_code {hex(hexop)}!")
            print(e.with_traceback())
            

        if self.delay_timer > 0:
            self.delay_timer -= 1

        if self.sound_timer > 0:
            self.sound_timer -= 1
        if self.pc >  0x400:    # 512 + 0x200 where pc begins
            print("Program counter out of bounce")
            print("Current value of pc:", self.pc)

    # All Cpu instructions/opcodes

    def op_0nnn(self):
        if self.op_code == 0x0:
            pygame.quit()
            sys.exit()
        if self.op_code == 0xe0:
            self.op_00E0()
            return
        extrop = self.op_code & 0xf00f

        try:
            self.opfunctions[extrop]()
        except:
            print(f"invalid op_code, {hex(self.op_code)}")
            self.pc += 2


    def op_00E0(self):
        # Clear the screen buffer
        self.display_buff = [0] * 64 * 32
        self.draw = True
        self.pc += 2
    def op_00EE(self):
        # Return from subroutine

        self.pc = self.stack[self.stack_ptr] + 2
        self.stack_ptr -= 1

    def op_1nnn(self):
        # Jump naar nnn

        self.pc = self.op_code & 0x0FFF

    def op_2nnn(self):
        # Call subroutine at nnn

        nnn = self.op_code & 0xfff
        self.stack_ptr += 1
        self.stack[self.stack_ptr] = self.pc
        self.pc = nnn
    def op_3xkk(self):
        # Skip instruction Vx == kk
        # Geen idee hou het werk GG chatGPT

        
        kk = self.op_code & 0x00FF  # Extract immediate value kk
        
        if self.registers[self.Vx] == kk:
            self.pc += 4
        else:
            self.pc += 2
    def op_4xkk(self):
        # Skip instruction Vx != kk

        kk = self.op_code & 0x00FF  # Extract immediate value kk
        if self.registers[self.Vx] != kk:
            self.pc += 4
        else:
            self.pc += 2
    def op_5xy0(self):
        if self.registers[self.Vx] == self.registers[self.Vy]:
            self.pc +=4
        else:
            self.pc += 2
    def op_6xkk(self):
        kk = self.op_code & 0x00FF
        self.registers[self.Vx] = kk
        self.pc += 2
    def op_7xkk(self):
        kk = self.op_code & 0x00FF
        self.registers[self.Vx] += kk
        self.registers[self.Vx] &= 0xff
        self.pc += 2
    def op_8xy0(self):
        self.registers[self.Vx] = self.registers[self.Vy]
        self.registers[self.Vx] &= 0xFF
        self.pc += 2
    def op_8xy1(self):
        val = self.registers[self.Vx] | self.registers[self.Vy]
        self.registers[self.Vx] = val
        self.registers[self.Vx] &= 0xFF
        self.pc += 2

    def op_8xy2(self):
        val = self.registers[self.Vx] & self.registers[self.Vy]
        self.registers[self.Vx] = val
        self.registers[self.Vx] &= 0xFF
        self.pc += 2
    def op_8xy3(self):
        val = self.registers[self.Vx] ^ self.registers[self.Vy]
        self.registers[self.Vx] = val
        self.registers[self.Vx] &= 0xFF
        self.pc += 2
    def op_8xy4(self):
        val = self.registers[self.Vx] + self.registers[self.Vy]
        if val > 0x00FF:
            self.registers[0xF] = 1
        else:
            self.registers[0xF] = 0

        self.registers[self.Vx] = val
        self.registers[self.Vx] &= 0xFF
        self.pc += 2

    def op_8xy5(self):
        if self.registers[self.Vx] < self.registers[self.Vy]:
            self.registers[15] = 0
        else:
            self.registers[15] = 1

        self.registers[self.Vx] -= self.registers[self.Vy]
        self.registers[self.Vx] &= 0xFF
        self.pc += 2

    def op_8xy6(self):
        self.registers[0xF] = self.registers[self.Vx] & 0x0001
        self.registers[self.Vx] = self.registers[self.Vx] >> 1
        self.registers[self.Vx] &= 0xFF
        self.pc += 2

    def op_8xy7(self):
        if self.registers[self.Vy] < self.registers[self.Vx]:
            self.registers[15] = 0
        else:
            self.registers[15] = 1

        self.registers[self.Vx] = self.registers[self.Vy] - self.registers[self.Vx]
        self.registers[self.Vx] &= 0xff
        self.pc += 2
    def op_8xyE(self):
        self.registers[0xF] = self.registers[self.Vx] >> 7
        self.registers[self.Vx] = self.registers[self.Vx] << 1
        self.pc += 2

    def op_9xy0(self):
        if self.registers[self.Vx] != self.registers[self.Vy]:
            self.pc += 4
        else:
            self.pc += 2
    def op_Annn(self):
        self.I = self.op_code & 0x0FFF
        self.pc += 2
    def op_Bnnn(self):
        self.pc = (self.op_code & 0x0FFF) + self.registers[0]
    def op_Cxkk(self):
        rand_num = random.randint(0, 255)
        kk = self.op_code & 0x00FF

        self.registers[self.Vx] = rand_num & kk
        self.pc += 2
    def op_Dxyn(self):
        x = self.registers[self.Vx]
        y = self.registers[self.Vy]
        self.registers[0xF] = 0
        height = self.op_code & 0x000F

        for h in range(height):
            pixel = self.memory[self.I + h]
            for w in range(8):
                if (pixel & (0x80 >> w)) != 0:

                    loc = (x + w + (h + y) * 64) % 2048

                    if self.display_class.display_buff[loc] == 1:
                        self.registers[0xf] = 1
                    self.display_class.display_buff[loc] ^= 1

        self.draw = True
        self.pc += 2


    def op_8nnn(self):
        if self.op_code & 0x000F == 0:
            self.op_8xy0()
            return

        try:
            self.opfunctions[self.op_code & 0xf00f]()
        except:
            print("Unknown instruction")
            self.pc += 2

    def op_Ennn(self):
        '''
        Decode Ennn-op_codes
        :return:
        '''
        try:
            self.opfunctions[self.op_code & 0xf00f]()
        except Exception as e:
            print(e.with_traceback())
            print(f"invalid op_code {hex(self.op_code)}")
    def op_Ex9E(self):
        if self.key_inputs[self.registers[self.Vx] & 0xf] != 0:
            self.pc += 4
        else:
            self.pc += 2
    def op_ExA1(self):
        if self.input_class.key_inputs[self.registers[self.Vx] & 0xf] == 0:
            self.pc += 4
        else:
            self.pc += 2

    def op_Fx07(self):
        self.registers[self.Vx] = self.delay_timer
        self.pc += 2
    def op_Fx0A(self):
        while (True):
            event = pygame.event.wait()
            if event.type == pygame.KEYDOWN:
                if event.key in self.input_class.keyset.keys():
                    self.key_inputs[self.keyset[event.key]] = 1
                    break
        self.pc += 2

    def op_Fx15(self):
        self.delay_timer = self.registers[self.Vx]
        self.pc += 2

    def op_Fx18(self):
        self.sound_timer = self.registers[self.Vx]
        self.pc += 2
    
    def op_Fx1E(self):
        self.I += self.registers[self.Vx]
        self.pc += 2

    def op_Fx29(self):
        self.I = (5 * (self.registers[self.Vx])) & 0x0FFF
        self.pc += 2

    def op_Fx33(self):
        self.memory[self.I] = self.registers[self.Vx] // 100
        self.memory[self.I + 1] = (self.registers[self.Vx] % 100) // 10
        self.memory[self.I + 2] = self.registers[self.Vx] % 10
        self.pc += 2
    
    def op_Fx55(self):
        i = 0
        while i <= self.Vx:
            self.memory[self.I + i] = self.registers[i]
            i += 1

        self.pc += 2

    def op_Fx65(self):
        i = 0
        while i <= self.Vx:
            self.registers[i] = self.memory[self.I + i] 
            i += 1

        self.pc += 2


    def op_Fnnn(self):
        '''
        Decode Fnnn-op_codes
        :return:
        '''
        try:
            self.opfunctions[self.op_code & 0xf0ff]()
        except Exception as e:
            print(" op_code was not valid why?")
            print(e.with_traceback())

class Input:
    def __init__(self, cpu_class, display_class):

        self.cpu_class = cpu_class
        self.display_class = display_class

        self.key_inputs = [0] * 16


        self.keyset = {
            pygame.K_1: 5,
            pygame.K_2: 2,
            pygame.K_3: 3,
            pygame.K_UP: 12,
            pygame.K_q: 8,
            pygame.K_w: 1,
            pygame.K_e: 6,
            pygame.K_DOWN: 13,
            pygame.K_a: 7,
            pygame.K_s: 4,
            pygame.K_d: 9,
            pygame.K_f: 14,
            pygame.K_z: 10,
            pygame.K_x: 0,
            pygame.K_b: 11,
            pygame.K_v: 15
        }
    
    def load_rom(self, file_path):
        try:
            with open(file_path, "rb") as rom_file:
                rom_data = rom_file.read()
                if len(rom_data) <= len(self.cpu_class.memory) - 0x200:
                    for i, val in enumerate(rom_data):
                        self.cpu_class.memory[i + 0x200] = val
                else:
                    print("Error: ROM file size exceeds available memory stack_ptr.")
        except FileNotFoundError:
            print("Error: ROM file not found.")
        except IOError:
            print("Error: Unable to read ROM file.")



class Display:
    def __init__(self, cpu_class):
        self.cpu_class = cpu_class
        
        self.draw = True
        self.timer = pygame.time.Clock()
        self.screen = pygame.display.set_mode((64 * 10, 32 * 10))
        self.display_buff = [0] * 64 * 32

        self.fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF8,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80,  # F
                ]
    def init_font(self):
        self.cpu_class.pc = 512
        for i in range(80):
            self.cpu_class.memory[i] = self.fontset[i]

    def drawScreen(self):
        pygame.init()
        black = (0, 0, 0)
        white = (255, 255, 255)
        self.screen.fill(black)
        for i in range(len(self.display_buff)):
                if self.display_buff[i] == 1:
                    pygame.draw.rect(self.screen, white, ((i % 64) * 10, (i / 64) * 10, 10,10))
                else:
                    pygame.draw.rect(self.screen, black, ((i % 64) * 10, (i / 64) * 10, 10,10))
        pygame.display.update()



def main():

    # Create instances of classes, otherwise class dependency error hell
    cpu_class = Cpu(None, None)
    display_class = Display(cpu_class)
    input_class = Input(cpu_class, display_class)  

    
    cpu_class.input_class = input_class
    cpu_class.display_class = display_class

    
    rompath = sys.argv[1]
    input_class.load_rom(rompath)
    display_class.init_font()

    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in input_class.keyset.keys():
                    input_class.key_inputs[input_class.keyset[event.key]] = 1
            elif event.type == pygame.KEYUP:
                if event.key in input_class.keyset.keys():
                    input_class.key_inputs[input_class.keyset[event.key]] = 0

        
        cpu_class.cpu_cycle()
        if cpu_class.display_class.draw:
            cpu_class.display_class.drawScreen()

        # Fps 240
        cpu_class.display_class.timer.tick(240)


if __name__ == "__main__":
    pygame.init()

    main()
