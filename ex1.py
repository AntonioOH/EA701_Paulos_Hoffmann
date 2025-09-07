from machine import Pin, PWM, I2C
import utime
from ssd1306 import SSD1306_I2C  # envie ssd1306.py para a placa

# ---------- Gerador PWM de teste na GPIO0 (substitua pelo seu, se quiser) ----------
pwm = PWM(Pin(0))
pwm.freq(1000)          # 1 kHz
pwm.duty_u16(32768)     # 50%

# ---------- Probe digital em GPIO1 ----------
sig = Pin(1, Pin.IN, Pin.PULL_DOWN)  # pull-down evita ruído se desconectar o jumper

# ---------- OLED no I2C1 (GPIO2=SDA, GPIO3=SCL) ----------
i2c = I2C(1, scl=Pin(3), sda=Pin(2))
oled = SSD1306_I2C(128, 64, i2c)

# ---------- Estado de medição ----------
last_rise_us = None
period_us = None
high_us = None

def both_edges(pin):
    """Um único handler atende subida e descida."""
    global last_rise_us, period_us, high_us
    now = utime.ticks_us()
    lvl = pin.value()
    if lvl:  # borda de SUBIDA -> calcula período (rise-to-rise)
        if last_rise_us is not None:
            period_us = utime.ticks_diff(now, last_rise_us)
        last_rise_us = now
    else:    # borda de DESCIDA -> calcula tempo em nível alto
        if last_rise_us is not None:
            high_us = utime.ticks_diff(now, last_rise_us)

# Registra UMA irq com os dois triggers
sig.irq(handler=both_edges, trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING)

def fmt(x): 
    return "{:.1f}".format(x)

last_show = utime.ticks_ms()
while True:
    f = 0.0
    duty = 0.0
    # Só calcula quando já temos um período e um high válidos
    if period_us and high_us and period_us > 0:
        f = 1_000_000.0 / period_us
        duty = (high_us / period_us) * 100.0
        if duty < 0: duty = 0.0
        if duty > 100: duty = 100.0

    # OLED (10 Hz)
    if utime.ticks_diff(utime.ticks_ms(), last_show) > 100:
        oled.fill(0)
        oled.text("Probe Digital", 0, 0)
        oled.text("GPIO0 -> GPIO1", 0, 12)
        oled.text("f = " + fmt(f) + " Hz", 0, 28)
        oled.text("duty = " + fmt(duty) + " %", 0, 44)
        oled.show()
        last_show = utime.ticks_ms()

    utime.sleep_ms(5)
