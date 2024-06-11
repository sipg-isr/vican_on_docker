import os
import torch
import numpy as np
from shapely.geometry import Polygon
import scipy.io as sio

from vican.cam import estimate_pose_mp
from vican.bipgo import bipartite_se3sync, object_bipartite_se3sync
from vican.dataset import Dataset

DATASET_PATH = '/dataset'

MARKER_SIZE = 0.48 * 0.575

MARKER_IDS = list(map(str, range(24)))

def main():
    dataset = Dataset(root=os.path.join(DATASET_PATH, 'room'))

    aux = torch.load(os.path.join(DATASET_PATH, 'cube_calib_pose.pt'))

    obj_pose_est = object_bipartite_se3sync(aux,
                                            noise_model_r=lambda edge : 0.01 * Polygon(zip(edge['corners'][:,0], edge['corners'][:,1])).area**2,
                                            noise_model_t=lambda edge : 0.001 * Polygon(zip(edge['corners'][:,0], edge['corners'][:,1])).area**6,
                                            edge_filter=lambda edge : edge['reprojected_err'] < 0.1,
                                            maxiter=4,
                                            lsqr_solver="conjugate_gradient",
                                            dtype=np.float64)
    
    cam_marker_edges = estimate_pose_mp(cams=dataset.im_data['cam'],
                                        im_filenames=dataset.im_data['filename'],
                                        aruco='DICT_4X4_1000',
                                        marker_size=MARKER_SIZE,
                                        corner_refine='CORNER_REFINE_APRILTAG',
                                        marker_ids=MARKER_IDS,
                                        flags='SOLVEPNP_IPPE_SQUARE',
                                        brightness=-150,
                                        contrast=120)
    
    torch.save(cam_marker_edges, os.path.join(DATASET_PATH, 'room_pose.pt'))

    tmax = 2000
    edges = {k : v for k, v in cam_marker_edges.items() if int(k[1].split('_')[0]) < tmax}

    pose_est = bipartite_se3sync(edges,
                                constraints=obj_pose_est,
                                noise_model_r=lambda edge : 0.001 * Polygon(zip(edge['corners'][:,0], edge['corners'][:,1])).area**1.0,
                                noise_model_t=lambda edge : 0.001 * Polygon(zip(edge['corners'][:,0], edge['corners'][:,1])).area**2.0,
                                edge_filter=lambda edge : edge['reprojected_err'] < 0.05,
                                maxiter=4,
                                lsqr_solver="conjugate_gradient",
                                dtype=np.float32)
    
    sio.savemat(os.path.join(DATASET_PATH, 'pose_est.mat'), pose_est)

if __name__ == "__main__":
    main()