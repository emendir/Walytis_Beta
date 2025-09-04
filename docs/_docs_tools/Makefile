clean:
	rm -r ../API-Reference  rm -r API-Reference/*.rst & rm -r _build &

api: clean
	./build_api_ref.sh


all: api
	./build_full_html.sh
