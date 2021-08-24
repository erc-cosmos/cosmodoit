#! /bin/bash

if [ $# -ne 2 ]; then
echo "Error in usage: $./align.sh ref(.xml) align(.mid)"
exit 1
fi

I1="`basename "$1"`"
I2="`basename "$2"`"
ProgramFolder="`dirname "$0"`/bin"
RelCurrentFolder="."

cp "$1.xml" "$2.mid" "${RelCurrentFolder}"
"$ProgramFolder/midi2pianoroll" 0 "$RelCurrentFolder/${I2}" > /dev/null

"$ProgramFolder/MusicXMLToHMM" "${1}.xml" "$RelCurrentFolder/${I1}_hmm.txt" > /dev/null
"$ProgramFolder/MusicXMLToHMM" "${1}.xml" "$RelCurrentFolder/${I1}_hmm.txt" > /dev/null
"$ProgramFolder/MusicXMLToFmt3x" "${1}.xml" "$RelCurrentFolder/${I1}_fmt3x.txt" > /dev/null

"$ProgramFolder/ScorePerfmMatcher" "$RelCurrentFolder/${I1}_hmm.txt" "$RelCurrentFolder/${I2}_spr.txt" "$RelCurrentFolder/${I2}_pre_match.txt" 0.01 > /dev/null
"$ProgramFolder/ErrorDetection" "$RelCurrentFolder/${I1}_fmt3x.txt" "$RelCurrentFolder/${I1}_hmm.txt" "$RelCurrentFolder/${I2}_pre_match.txt" "$RelCurrentFolder/${I2}_err_match.txt" 0 > /dev/null
"$ProgramFolder/RealignmentMOHMM" "$RelCurrentFolder/${I1}_fmt3x.txt" "$RelCurrentFolder/${I1}_hmm.txt" "$RelCurrentFolder/${I2}_err_match.txt" "$RelCurrentFolder/${I2}_realigned_match.txt" 0.3 > /dev/null

mv "$RelCurrentFolder/${I2}_realigned_match.txt" "$RelCurrentFolder/${I2}_match.txt"

#rm "$RelCurrentFolder/${I2}_err_match.txt"
#rm "$RelCurrentFolder/${I2}_pre_match.txt"
