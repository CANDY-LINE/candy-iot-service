deploy:
	./install.sh pack && \
	scp ./candy-iot-service-*.tgz root@edison.local:~
