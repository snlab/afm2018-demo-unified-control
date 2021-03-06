# @TEST-REQUIRES: which python
# @TEST-REQUIRES: which curl
#
# @TEST-EXEC: btest-bg-run httpd python $SCRIPTS/httpd.py --max 2 --addr=127.0.0.1
# @TEST-EXEC: sleep 3
# @TEST-EXEC: btest-bg-run bro bro -b %INPUT
# @TEST-EXEC: btest-bg-wait 15
# @TEST-EXEC: cat bro/.stdout | sort >output
# @TEST-EXEC: btest-diff output

@load base/utils/active-http
redef exit_only_after_terminate = T;

global c: count = 0;

function check_exit_condition()
	{
	c += 1;

	if ( c == 2 )
		terminate();
	}

function test_request(label: string, req: ActiveHTTP::Request)
	{
	when ( local response = ActiveHTTP::request(req) )
		{
		print label, response;
		check_exit_condition();
		}
	timeout 1min
		{
		print "HTTP request timeout";
		check_exit_condition();
		}
	}

event bro_init()
	{
	test_request("test1", [$url="127.0.0.1:32123"]);
	test_request("test2", [$url="127.0.0.1:32123/empty", $method="POST"]);
}