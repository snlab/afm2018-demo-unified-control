@load base/protocols/http/main
@load base/utils/files
@load ./trident.bro

event http_header(c: connection, orig: bool, name: string, value: string) {
    if (/^[hH][oO][sS][tT]$/ in name) {
    	print c;
        Trident::report(c, "http_uri", c$http$uri);
        print "host: " + value;
        print "http_uri: " + c$http$uri;
    }
}
