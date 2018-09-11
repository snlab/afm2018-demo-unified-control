#include <stdlib.h>
#include <stdio.h>
#include <curl/curl.h>

#define MICROSECOND_TO_SECOND 1000000L

static double GRACEFUL_PERIOD = 50000; /* default to 50ms */

struct task_progress {
	CURL *curl;

	double timestamp;
	curl_off_t to_be_downloaded;
	curl_off_t to_be_uploaded;
	curl_off_t downloaded;
	curl_off_t uploaded;
};

static int update_progress(struct task_progress *progress, double current, 
				curl_off_t _d, curl_off_t downloaded,
				curl_off_t _u, curl_off_t uploaded) {
	long interval;
	double download_speed, upload_speed;
	double download_percentage, upload_percentage;

	interval = (long)((current - progress->timestamp) * MICROSECOND_TO_SECOND);

	progress->to_be_downloaded = _d;
	progress->to_be_uploaded = _u;

	if (interval < GRACEFUL_PERIOD) {
		return 0;
	}

	download_speed = (double)(downloaded - progress->downloaded) / interval;
	upload_speed = (double)(uploaded - progress->uploaded) / interval;

	download_percentage = (downloaded) / (_d + 1e-10);
	upload_percentage = (uploaded) / (_u + 1e-10);

	progress->timestamp = current;
	progress->downloaded = downloaded;
	progress->uploaded = uploaded;

	fprintf(stderr, "%.2f %.5f %.5f %.5f %.5f\r\n",
			current * MICROSECOND_TO_SECOND,
			download_speed, upload_speed,
			download_percentage, upload_percentage);

	return 0;
}

static int report_progress(void *p,
	 curl_off_t _d, curl_off_t downloaded,
	 curl_off_t _u, curl_off_t uploaded) {
	struct task_progress *progress = (struct task_progress *)p;
	CURL *curl = progress->curl;

	double current = 0;

	curl_easy_getinfo(curl, CURLINFO_TOTAL_TIME, &current);

	return update_progress(p, current, _d, downloaded, _u, uploaded);
}

int main(int argc, char** argv) {
	if (argc < 3) {
		fprintf(stderr, "Usage: %s URL GRACEFUL_PERIOD\r\n", argv[0]);
		return 1;
	}
	CURL *curl;
	CURLcode error = CURLE_OK;
	struct task_progress progress;

	GRACEFUL_PERIOD = atoi(argv[2]);

	curl = curl_easy_init();
	if (curl) {
		progress.curl = curl;
		progress.timestamp = 0;
		progress.uploaded = 0;
		progress.downloaded = 0;
		progress.to_be_downloaded = 0;
		progress.to_be_uploaded = 0;

		curl_easy_setopt(curl, CURLOPT_URL, argv[1]);

		curl_easy_setopt(curl, CURLOPT_XFERINFOFUNCTION, report_progress);
		curl_easy_setopt(curl, CURLOPT_XFERINFODATA, &progress);

		curl_easy_setopt(curl, CURLOPT_NOPROGRESS, 0L);

		error = curl_easy_perform(curl);

		if (error != CURLE_OK) {
			fprintf(stderr, "# %s\n", curl_easy_strerror(error));
		} else {
			double diff = (GRACEFUL_PERIOD * 1.0) / MICROSECOND_TO_SECOND;
			update_progress(&progress, progress.timestamp + diff,
					progress.to_be_downloaded, progress.to_be_downloaded,
					progress.to_be_uploaded, progress.to_be_uploaded);
		}

		/* always cleanup */
		curl_easy_cleanup(curl);
	}
	return (int)error;
}
