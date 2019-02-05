from torchvision import transforms, datasets
import torch
import os
import sys
import random
import torch.utils.data


def get_data(in_size, data_dir, val_only=False, batch_size=128,
             class_sz=-1, seed=random.randint(0, 10000), perturb=True,
             num_workers=4, iter_size=1, distributed=False):
    """ Provides a pytorch loader to load in imagenet
    Args:
        in_size (int): the input size - can be used to scale the spatial size
        data_dir (str): the directory where the data is stored
        val_only (bool): Whether to load only the validation set
        batch_size (int): batch size for train loader. the val loader batch
            size is always 100
        class_sz (int): size of the training set. can be used to subsample it
        seed (int): random seed for the loaders
        perturb (bool): whether to do data augmentation on the training set
        num_workers (int): how many workers to load data
        iter_size (int):
    """
    # Set the loader initializer seeds for reproducibility
    def worker_init_fn(id):
        import random
        import numpy as np
        random.seed(seed+id)
        np.random.seed(seed+id)

    traindir = os.path.join(data_dir, 'train')
    valdir = os.path.join(data_dir, 'val2')
    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                     std=[0.229, 0.224, 0.225])

    if not os.path.exists(valdir):
        raise ValueError(
            'Could not find the val2 folder in the Tiny Imagenet directory.' 
            'Have you run the prep_tinyimagenet.py script in '
            'invariant_convolution.data?')

    # Get the test loader
    transform_test = transforms.Compose([
        transforms.CenterCrop(in_size),
        transforms.ToTensor(),
        normalize
    ])
    testloader = torch.utils.data.DataLoader(
        datasets.ImageFolder(valdir, transform_test),
        batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True,
        worker_init_fn=worker_init_fn)

    if val_only:
        trainloader = None
    else:
        # Get the train loader
        if perturb:
            transform_train = transforms.Compose([
                transforms.RandomCrop(in_size, padding=8),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                normalize,
            ])
        else:
            transform_train = transforms.Compose([
                transforms.CenterCrop(in_size),
                transforms.ToTensor(),
                normalize
            ])

        trainset = datasets.ImageFolder(
            traindir, transform_train)

        if distributed:
            trainsampler = torch.utils.data.distributed.DistributedSampler(
                trainset)
        else:
            trainsampler = None

        trainloader = torch.utils.data.DataLoader(
            trainset, batch_size=batch_size // iter_size,
            shuffle=(trainsampler is None), num_workers=num_workers,
            pin_memory=True, sampler=trainsampler,
            worker_init_fn=worker_init_fn)

    sys.stdout.write("| loaded tiny imagenet")
    return trainloader, testloader
