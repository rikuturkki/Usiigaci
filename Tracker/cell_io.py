# Author: ImagineA / Andrei Rares
# Date: 2018-08-18

import pims
import numpy as np
from os.path import join, split, normpath, exists
from os import makedirs
from datetime import datetime
from cell_img_proc import create_colorized_masks, create_colorized_tracks, create_track_overview
from imageio import imwrite, mimwrite
import logging


def read_img_sequence(path, file_extension):
    pims_sequence = pims.ImageSequence(join(path, '*.{}'.format(file_extension)), process_func=None)
    return np.stack([frame.copy() for frame in pims_sequence], axis=2)


def save_results(path_in, trj, col_tuple, id_masks, cell_ids, background_id,
                 color_list, cell_color_idx, cell_visibility,
                 show_ids, show_contours, show_tracks,
                 mask_extension):
    # Create output folder based on input path and experiment date/time
    save_time = datetime.now()  # Experiment time
    root_path, folder_in = split(normpath(path_in))
    path_out = join(root_path,
                    '{}_Exp_{}-{:02d}-{:02d}T{:02d}{:02d}{:02d}'.format(
                        folder_in,
                        save_time.year, save_time.month, save_time.day,
                        save_time.hour, save_time.minute, save_time.second))
    if not exists(path_out):
        makedirs(path_out)

    # Save CSV results
    save_results_to_csv(path_out, trj, col_tuple, cell_visibility)

    # Save id masks (may be useful for later postprocessing
    logging.info('================= Saving id masks frame by frame =================')
    save_sequence_frame_by_frame([id_masks[:, :, i_frame] for i_frame in range(id_masks.shape[2])],
                                 path_out, 'Id_masks_per_frame', mask_extension, 'id_masks')

    # Save colorized masks
    colorized_masks = create_colorized_masks(id_masks, trj, cell_ids, background_id,
                                             color_list, cell_color_idx,
                                             cell_visibility, show_ids)
    logging.info('================= Saving colorized masks frame by frame =================')
    save_sequence_frame_by_frame(colorized_masks, path_out, 'Masks_per_frame', mask_extension, 'masks')
    logging.info('================= Saving colorized masks as animation =================')
    mimwrite(join(path_out, 'masks_animation.mp4'), colorized_masks, macro_block_size=None)

    # Save colorized tracks
    colorized_tracks = create_colorized_tracks(id_masks, trj, cell_ids, background_id,
                                               color_list, cell_color_idx,
                                               cell_visibility, show_ids, show_contours, show_tracks,
                                               True)
    logging.info('================= Saving colorized tracks frame by frame =================')
    save_sequence_frame_by_frame(colorized_tracks, path_out, 'Tracks_per_frame', mask_extension, 'tracks')
    logging.info('================= Saving colorized tracks as animation =================')
    mimwrite(join(path_out, 'tracks_animation.mp4'), colorized_tracks, macro_block_size=None)

    # Save complete tracks
    logging.info('================= Saving track overview =================')
    all_tracks = create_track_overview(id_masks, trj, cell_ids, background_id,
                                       color_list, cell_color_idx,
                                       cell_visibility, show_ids,
                                       True)
    imwrite(join(path_out, 'all_tracks.{}'.format(mask_extension)), all_tracks)
    logging.info('Saving finished.')


def save_results_to_csv(path_out, trj, col_tuple, cell_visibility):
    cols_to_save = ['particle'] + col_tuple['original'] + col_tuple['weighted'] + col_tuple['extra']
    order_list = ['particle', 'frame']
    trj[trj['particle'].isin([cell_id
                              for cell_id, show_cell in cell_visibility.items()
                              if show_cell])].sort_values(order_list).to_csv(
        join(path_out, 'tracks.csv'),
        columns=cols_to_save,
        float_format='%.03f',  # This is for 3 digits after the comma. For unlimited digits use '%f'
        index=False)


def save_sequence_frame_by_frame(sequence, path_out, sequence_folder, file_extension, file_prefix):
    path_out_sequence = join(path_out, sequence_folder)
    if not exists(path_out_sequence):
        makedirs(path_out_sequence)
    n_frames = len(sequence)
    max_n_digits = 1 + int(np.floor(np.log10(n_frames - 1)))
    for i_frame, frame in enumerate(sequence):
        logging.info('Frame {}...'.format(i_frame))
        frame_name = '{}_{}.{}'.format(file_prefix, str(i_frame).zfill(max_n_digits), file_extension)
        imwrite(join(path_out_sequence, frame_name), frame)
