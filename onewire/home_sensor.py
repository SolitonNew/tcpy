class HomeSensor(object):
    CMD_READ_DATA = 0xA0
    
    def __init__(self, onewire):
        self.ow = onewire
        self.roms = []
        
    def search(self):
        self.roms = []        
        for rom in self.ow.search():
            if rom[0] == 0xF0:
                self.roms += [rom]
                
        return self.roms

    def _get_first(self):
        if len(self.roms) == 0:
            self.search()

        if len(self.roms) > 0:
            return self.roms[0]
        else:
            return None
        
    def get_data(self, rom = False):
        if not self.ow.reset():
            return False
        
        if not rom:
            rom = self._get_first()
            
        if rom:
            self.ow.match_rom(rom)
            self.ow.write_byte(self.CMD_READ_DATA)
        else:
            return False
        
        buff = bytearray(2)
        for i in range(2):
            buff[i] = self.ow.read_byte()

        if self.ow.crc8(buff):
            return False

        return buff[0]
