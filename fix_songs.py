#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import argparse
import os
import shutil
import datetime

from glob import glob

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--dir', default=os.getcwd())
parser.add_argument('-i', '--ignore-errors', default=False, action='store_true')
parser.add_argument('-r', '--recurse-dirs', default=False, action='store_true')
parser.add_argument('-m', '--max-recurse', default=3)


args = parser.parse_args()
dirs = os.listdir(args.dir)

RUNTIME = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")

warnings = []


def fix_song(folder_path, num_recurses = 0):
    errored = False
    try:
        print("Checking {}".format(folder_path))

        info_file = os.path.join(folder_path, 'info.json')
        with open(info_file) as fp:
            manifest = json.load(fp)
        
    except FileNotFoundError:
        if not args.ignore_errors:
            warning = "WARNING: Couldn't parse manifest for: {}".format(folder_path)
            warn(warning)
            return False
        errored = True
    except UnicodeEncodeError:
        # Unicode is hard, windows console sucks, skip this song
        return False
    except json.JSONDecodeError:
        # There are some songs with messed up info files, lets just ignore those
        return False
    
    # so we can recurse without being in an error handler
    if errored:
        if args.recurse_dirs and num_recurses < args.max_recurse:
            subfolders = os.listdir(folder_path)
            for subfolder in subfolders:
                if os.path.isdir(subfolder):
                    fix_song(os.path.join(folder_path, subfolder))
        return
    
    # read the BPM
    info_bpm = manifest["beatsPerMinute"]
    
    
    # get the difficulty levels
    difficulties = manifest["difficultyLevels"]
    
    # Read their BPMs
    bpms = set()
    
    for difficulty in difficulties:
        try:
            with open(os.path.join(folder_path, difficulty["jsonPath"])) as fp:
                difficulty_manifest = json.load(fp)
            bpms.add(difficulty_manifest["_beatsPerMinute"])
        except FileNotFoundError as e:
            
            warn("WARNING: Difficulty {} not found in {}".format(difficulty, folder_path))
                
        
    if len(bpms) > 1:
        warn("WARNING: More than one BPM setting for song {}, difficulties have different speeds. This won't work until a proper patch is released".format(folder_path))
        if not args.ignore_errors:
            raise ValueError
    
    if len(bpms) == 0: 
        warn("WARNING: No difficulties specified in {}. Wat".format(folder_path))
        
    # Backup and Update info.json if necessary
    song_bpm = bpms.pop()
    if song_bpm != info_bpm:
        print("BPM in song file ({}) and info file ({}) differ; patching".format(song_bpm, info_bpm))
        
        shutil.copy(info_file, "{}{}.bak".format(info_file, RUNTIME))
        
        manifest["beatsPerMinute"] = song_bpm
        with open(info_file, 'w') as fp:
            json.dump(manifest, fp)
        
def warn(warning_str):
    global warnings
    warnings.append(warning_str)
    print(warning_str)

        
if __name__ == '__main__':
    fix_song(args.dir)
    
    print("------------Run Finished-------------")
    for warning in warnings:
        print(warning)