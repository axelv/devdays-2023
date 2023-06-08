set -e

function download_r4b() {
	curl --output definitions.json.zip https://hl7.org/fhir/R4B/definitions.json.zip
	shasum --algorithm 256 --check r4b.bundle.checksumfile
	unzip definitions.json.zip "definitions.json/profiles-types.json" "definitions.json/profiles-resources.json"
	mv -v definitions.json/profiles-types.json fhir.r4b.types.json
	mv -v definitions.json/profiles-resources.json fhir.r4b.resources.json

	rm -rf definitions.json/
	rm definitions.json.zip
}

function download_r5() {
	curl --output definitions.json.zip https://hl7.org/fhir/R5/definitions.json.zip
	shasum --algorithm 256 --check r5.bundle.checksumfile
	unzip definitions.json.zip "profiles-types.json" "profiles-resources.json"
	mv -v profiles-types.json fhir.r5.types.json
	mv -v profiles-resources.json fhir.r5.resources.json

	rm definitions.json.zip
}

case "$1" in
	"r5")
		download_r5
	;;
	*)
		download_r4b
	;;
esac
