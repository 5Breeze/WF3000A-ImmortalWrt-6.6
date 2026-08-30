
define Device/kst_wf3000a
  DEVICE_VENDOR := KST
  DEVICE_MODEL := WF3000A
  DEVICE_VARIANT := NMBM 248MiB layout
  DEVICE_DTS := mt7981b-kst-wf3000a
  DEVICE_DTS_DIR := ../dts
  SUPPORTED_DEVICES := kst,wf3000a
  UBINIZE_OPTS := -E 5
  BLOCKSIZE := 128k
  PAGESIZE := 2048
  IMAGE_SIZE := 248320k
  KERNEL_IN_UBI := 1
  IMAGES += factory.bin
  IMAGE/factory.bin := append-ubi | check-size $$$$(IMAGE_SIZE)
  IMAGE/sysupgrade.bin := sysupgrade-tar | append-metadata
endef
TARGET_DEVICES += kst_wf3000a
