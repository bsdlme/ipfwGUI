PROGRAM             = ipfwGUI.py
DESKTOP_FILE	    = ${PROGRAM:C/.py//}.desktop
PREFIX             ?= /usr/local
BINDIR              = ${DESTDIR}${PREFIX}/bin
APPSDIR             = ${DESTDIR}${PREFIX}/share/applications
BSD_INSTALL_DATA   ?= install -m 0644
BSD_INSTALL_SCRIPT ?= install -m 555

all:

install: 
	${BSD_INSTALL_SCRIPT} ${PROGRAM} ${BINDIR}/${PROGRAM:C/.py//}
	if [ ! -d ${APPSDIR} ]; then mkdir -p ${APPSDIR}; fi
	${BSD_INSTALL_DATA} ${DESKTOP_FILE} ${APPSDIR}
clean:
	-rm -rf __pycache__
