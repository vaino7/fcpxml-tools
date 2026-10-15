# fcpxml-tools
The main purpose of this repository is to give everyone tools that catalyze editors' process. They entirely work with the XML file so it's pure logic + heuristics + xml manipulation

## Subtitle-Fixer `fixSubtitle.py`
This script is designed to fix subtitles mismatches and it does so by analyzing the subtitles generated within FCP and comparing them to the original ones: the idea is to find the starting and ending word of the generated subtitles and substitute them with the original ones but within the same timecode of the first error.

A marker is also set when keywords (like "EMPHASIS") are found in the original subtitles, allowing the editor to quickly spot them on the timeline.

## What's next?
- [ ] Create a tool that automatically places footage in the timeline based on the keyowords and timings (this tool should be called 'media-to-subs-syncronizer.py' or something like that)