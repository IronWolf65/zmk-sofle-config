**English** | [Русский](README.ru.md)

# ZMK Config for Sofle Choc (AliExpress/PandaKB)

This is a [ZMK Firmware](https://zmk.dev/) configuration for the **Sofle Choc** split keyboard.

**Kit:** Sofle Choc  
**Controller:** SuperMini nRF52840

## Hardware

- Encoder EC11 (low profile)
- OLED 128x32
- LED
- Battery
- Touchpad TPS43

## Building Firmware

Firmware can be built automatically using **GitHub Actions** in this repository. Pre-built `.uf2` files will be available in the [Actions](https://github.com/IronWolf65/zmk-sofle-config/actions) runs or in the `output/` directory after a successful build.

## Local Build

For local firmware build, use [zmk-docker-build](https://github.com/IronWolf65/zmk-docker-build).  
Run `make build`.

## Resources

- [ZMK Documentation](https://zmk.dev/docs)
- [ZMK Keymaps Guide](https://zmk.dev/docs/keymaps)
