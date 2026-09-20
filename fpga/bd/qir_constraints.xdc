# PYNQ-Z2 pin kisitlari — qir_kernel bitstream'i (gorev T015)
#
# Bu tasarim PL'de yalniz qir_kernel'i barindirir; disariya cikan TEK arayuz
# PS I2C0'in EMIO uzerinden verilen hattidir (karar K2, research.md §R5).
# LED, anahtar, HDMI, ses gibi cevre birimleri KULLANILMIYOR — kisitlari da
# yazilmiyor, cunku karsiligi olmayan porta kisit yazmak sentezi durdurur.
#
# --------------------------------------------------------------------------
# PIN KAYNAGI (tahmin DEGIL)
# --------------------------------------------------------------------------
# Xilinx/PYNQ deposu, PYNQ-Z2 base tasarimi:
#   boards/Pynq-Z2/base/vivado/constraints/base.xdc
#   https://github.com/Xilinx/PYNQ  (2026-09-20'de okundu)
#
# ⚠️ O dosyada UC ayri I2C var ve yanlisini secmek sessiz bir donanim hatasidir:
#
#   IIC_1                 U9 / T9    -> KART UZERINDEKI SES KODEKI (ADAU1761).
#                                        Disariya acik DEGIL. Buraya baglamak
#                                        kodekle veri yolu cakismasi demektir.
#   hdmi_in_ddc           U14 / U15  -> HDMI DDC. Bizim isimiz degil.
#   arduino_direct_iic    P15 / P16  -> Arduino baslinin ozel SDA/SCL hatti.
#                                        ✅ Disariya acik olan bu.
#
# Secilen: Arduino basligi. INA219 breakout'u oraya baglanir; ayni baslikta
# 3V3 ve GND de var.
# --------------------------------------------------------------------------

## PS I2C0 (EMIO) -> Arduino basligi SDA/SCL
set_property -dict {PACKAGE_PIN P15 IOSTANDARD LVCMOS33} [get_ports IIC_0_scl_io]
set_property -dict {PACKAGE_PIN P16 IOSTANDARD LVCMOS33} [get_ports IIC_0_sda_io]

# Ic zayif pull-up'lar. I2C acik-drenajdir ve yukari cekilmezse hat hic
# yukselmez. Bunlar ~10-50 kOhm mertebesindedir ve 100 kHz'de tek basina
# YETERSIZ kalabilir — INA219 breakout kartlari genelde 10 kOhm harici
# pull-up tasir ve asil is onlarindir. PYNQ base tasarimi da ayni sekilde
# hem iciyi aciyor hem hariciye guveniyor.
set_property PULLUP true [get_ports IIC_0_scl_io]
set_property PULLUP true [get_ports IIC_0_sda_io]
