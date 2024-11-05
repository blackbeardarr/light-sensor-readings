from machine import ADC, Pin

class LightSensor:
    MAX_VALUE = 65535  # 16-bit ADC resolution
    
    def __init__(self, pin):
        self.adc = ADC(Pin(pin))
    
    def read(self):
        """Returns raw ADC value"""
        return self.adc.read_u16()
    
    def read_percentage(self):
        """Returns light level as percentage"""
        return round((self.read() / self.MAX_VALUE) * 100, 1)