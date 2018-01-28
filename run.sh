searches=( 'something', 'somethingelse')
SLACK_API_TOKEN=''
SLACK_CHANNEL='moritz'

for i in "${searches[@]}"
do
	echo -e "Suche $i..."
        docker run -d --rm \
        -e "SLACK_API_TOKEN=${SLACK_API_TOKEN}" \
        -e "SLACK_CHANNEL=${SLACK_CHANNEL}" \
        -v ~/.moritz:/usr/src/app/data \
        -it moritz:latest python3 moritz.py --search="$i"
done
