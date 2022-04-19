cmake_minimum_required(VERSION 3.10)

project(Alignment)

# add the executables
add_executable(ErrorDetection ErrorDetection_v190702.cpp)
add_executable(RealignmentMOHMM RealignmentMOHMM_v170427.cpp)
add_executable(ScorePerfmMatcher ScorePerfmMatcher_v170101_2.cpp)
add_executable(midi2pianoroll midi2pianoroll_v170504.cpp)
add_executable(MusicXMLToFmt3x MusicXMLToFmt3x_v170104.cpp)
add_executable(MusicXMLToHMM MusicXMLToHMM_v170104.cpp)
add_executable(SprToFmt3x SprToFmt3x_v170225.cpp)
add_executable(Fmt3xToHmm Fmt3xToHmm_v170225.cpp)
add_executable(MatchToCorresp MatchToCorresp_v170918.cpp)

# install
install(TARGETS ErrorDetection RealignmentMOHMM ScorePerfmMatcher midi2pianoroll MusicXMLToFmt3x MusicXMLToHMM SprToFmt3x Fmt3xToHmm MatchToCorresp
    RUNTIME DESTINATION music_features/bin)