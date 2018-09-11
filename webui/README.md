## Kytos WebUI

### How to run

1. Download the [ui.zip](https://github.com/snlab/afm2018-demo-unified-control/raw/master/webui/ui.zip) and unzip it.
2. In the directory which includes `index.html`, start up a http server A at port B by command such as `python -m SimpleHTTPServer 8080`
3. In your browser, open the url http://\<address-of-server-A\>:B?/remote=\<address-of-SDN-controller\>

### Example

the SDN controller runs in the Virtual Machine which can be access by IP 192.168.1.105, 
the http server run at local machine port 8080, then you can access the WebUI by. http://localhost:8080/?remote=192.168.1.105



