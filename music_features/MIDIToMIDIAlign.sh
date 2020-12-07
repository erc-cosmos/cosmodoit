#! /bin/bash

if [ $# -ne 2 ]; then
echo "Error in usage: $./align.sh ref(.xml) align(.mid)"
exit 1
fi

I1="`basename "$1"`"
I2="`basename "$2"`"
ProgramFolder="`dirname "$0"`/bin"
RelCurrentFolder="."

cp "$1.mid" "$2.mid" "${RelCurrentFolder}"
"$ProgramFolder/midi2pianoroll" 0 "$RelCurrentFolder/${I1}"
"$ProgramFolder/midi2pianoroll" 0 "$RelCurrentFolder/${I2}"

"$ProgramFolder/SprToFmt3x" "${I1}_spr.txt" "${I1}_fmt3x.txt"
"$ProgramFolder/Fmt3xToHmm" "${I1}_fmt3x.txt" "${I1}_hmm.txt"

"$ProgramFolder/ScorePerfmMatcher" "$RelCurrentFolder/${I1}_hmm.txt" "$RelCurrentFolder/${I2}_spr.txt" "$RelCurrentFolder/${I2}_pre_match.txt" 0.01
"$ProgramFolder/ErrorDetection" "$RelCurrentFolder/${I1}_fmt3x.txt" "$RelCurrentFolder/${I1}_hmm.txt" "$RelCurrentFolder/${I2}_pre_match.txt" "$RelCurrentFolder/${I2}_err_match.txt" 0
"$ProgramFolder/RealignmentMOHMM" "$RelCurrentFolder/${I1}_fmt3x.txt" "$RelCurrentFolder/${I1}_hmm.txt" "$RelCurrentFolder/${I2}_err_match.txt" "$RelCurrentFolder/${I2}_realigned_match.txt" 0.3

# "$ProgramFolder/MatchToCorresp" "${I2}_match.txt" "${I1}_spr.txt" "${I2}_corresp.txt"

mv "$RelCurrentFolder/${I2}_realigned_match.txt" "$RelCurrentFolder/${I2}_match.txt"

rm "$RelCurrentFolder/${I2}_err_match.txt"
rm "$RelCurrentFolder/${I2}_pre_match.txt"
