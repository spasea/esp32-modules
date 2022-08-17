# Installing a package
- `make clean-frozen`
- `micropython -m upip install -p modules package_name`
- `make clean`
- `make`
  
# Deploy firmware
- `PORT=/dev/tty.usbserial-0001 make deploy`