# Copyright (c) Alibaba, Inc. and its affiliates.

import os
from multiprocessing.dummy import Pool as ThreadPool

from tqdm import tqdm

from .oss_utils import OssUtilities


class DatasetUploadManager(object):

    def __init__(self, dataset_name: str, namespace: str, version: str):
        from modelscope.hub.api import HubApi
        _hub_api = HubApi()
        _cookies = _hub_api.check_cookies_upload_data(use_cookies=True)
        _oss_config = _hub_api.get_dataset_access_config_session(
            cookies=_cookies,
            dataset_name=dataset_name,
            namespace=namespace,
            revision=version)

        self.oss_utilities = OssUtilities(_oss_config)

    def upload(self, object_name: str, local_file_path: str) -> str:
        object_key = self.oss_utilities.upload(
            oss_object_name=object_name,
            local_file_path=local_file_path,
            indicate_individual_progress=True)
        return object_key

    def upload_dir(self, object_dir_name: str, local_dir_path: str,
                   num_processes: int, chunksize: int,
                   filter_hidden_files: bool) -> int:

        def run_upload(args):
            self.oss_utilities.upload(
                oss_object_name=args[0],
                local_file_path=args[1],
                indicate_individual_progress=False)

        files_list = []
        for root, dirs, files in os.walk(local_dir_path):
            for file_name in files:
                if filter_hidden_files and file_name.startswith('.'):
                    continue
                # Concatenate directory name and relative path into a oss object key. e.g., train/001/1_1230.png
                object_name = os.path.join(
                    object_dir_name,
                    root.replace(local_dir_path, '', 1).strip('/'), file_name)

                local_file_path = os.path.join(root, file_name)
                files_list.append((object_name, local_file_path))

        with ThreadPool(processes=num_processes) as pool:
            result = list(
                tqdm(
                    pool.imap(run_upload, files_list, chunksize=chunksize),
                    total=len(files_list)))

        return len(result)
