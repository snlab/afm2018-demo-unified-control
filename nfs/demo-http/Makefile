LIBS=$(shell curl-config --libs)

democlient: curl_progress.o curl_progress.c
	gcc $< $(LIBS) -o democlient

clean:
	rm -rf democlient curl_progress.o
