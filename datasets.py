import torch
import torchvision.datasets as datasets
import torchvision.transforms as transforms
from torch.utils.data import Dataset
from celeba import CelebA, FFHQ
from eegDatasetClass import EEGDataset
from splitterClass import Splitter
import torch.distributed as dist
dist.init_process_group('gloo', init_method='file:///tmp/somefile', rank=0, world_size=1)

class ImageDataset(object):
    def __init__(self, args, cur_img_size=None, bs=None):
        bs = args.dis_batch_size if bs == None else bs
        img_size = cur_img_size if args.fade_in > 0 else args.img_size
        if args.dataset.lower() == 'cifar10':
            Dt = datasets.CIFAR10
            transform = transforms.Compose([
                transforms.Resize(size=(img_size, img_size)),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
            ])
            args.n_classes = 0
            train_dataset = Dt(root=args.data_path, train=True, transform=transform, download=True)
            val_dataset = Dt(root=args.data_path, train=False, transform=transform)

            train_sampler = torch.utils.data.distributed.DistributedSampler(train_dataset)
            val_sampler = torch.utils.data.distributed.DistributedSampler(val_dataset)
            self.train_sampler = train_sampler
            self.train = torch.utils.data.DataLoader(
                train_dataset,
                batch_size=args.dis_batch_size, shuffle=(train_sampler is None),
                num_workers=args.num_workers, pin_memory=True, sampler=train_sampler)

            self.valid = torch.utils.data.DataLoader(
                val_dataset,
                batch_size=args.dis_batch_size, shuffle=False,
                num_workers=args.num_workers, pin_memory=True, sampler=val_sampler)

            self.test = self.valid

        elif args.dataset.lower() == 'stl10':
            Dt = datasets.STL10
            transform = transforms.Compose([
                transforms.Resize(img_size),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
            ])

            train_dataset = Dt(root=args.data_path, split='train+unlabeled', transform=transform, download=True)
            val_dataset = Dt(root=args.data_path, split='test', transform=transform)
            if args.distributed:
                train_sampler = torch.utils.data.distributed.DistributedSampler(train_dataset)
                val_sampler = torch.utils.data.distributed.DistributedSampler(val_dataset)
            else:
                train_sampler = None
                val_sampler = None
            self.train_sampler = train_sampler
            self.train = torch.utils.data.DataLoader(
                train_dataset,
                batch_size=args.dis_batch_size, shuffle=(train_sampler is None),
                num_workers=args.num_workers, pin_memory=True, sampler=train_sampler)

            self.valid = torch.utils.data.DataLoader(
                val_dataset,
                batch_size=args.dis_batch_size, shuffle=False,
                num_workers=args.num_workers, pin_memory=True, sampler=val_sampler)

            self.test = self.valid

        elif args.dataset.lower() == 'eegdataset':      # **MODIFICA1: IMPORT EEGDataset and Splitter CLASS**
            Dt = EEGDataset

            train_dataset = Dt(eeg_signals_path=args.eeg_dataset)
            val_dataset = Dt(eeg_signals_path=args.eeg_dataset)

            train_sampler = torch.utils.data.distributed.DistributedSampler(train_dataset)
            val_sampler = torch.utils.data.distributed.DistributedSampler(val_dataset)
            self.train_sampler = train_sampler

            #self.train = {split: torch.utils.data.DataLoader(Splitter(
            #    train_dataset,
            #    split_path=args.splits_path,
            #    split_num=args.split_num,
            #    split_name=split),
            #    batch_size=args.dis_batch_size,
            #    shuffle=(train_sampler is None),
            #    num_workers=args.num_workers, pin_memory=True, drop_last=True, sampler=train_sampler) for split in
            #    ["train", "val", "test"]}

            self.train = torch.utils.data.DataLoader(Splitter(
                train_dataset,
                split_path=args.splits_path,
                split_num=args.split_num),
                batch_size=args.dis_batch_size,
                shuffle=(train_sampler is None),
                num_workers=args.num_workers, pin_memory=True, drop_last=True, sampler=train_sampler)

            self.valid = torch.utils.data.DataLoader(Splitter(
                val_dataset,
                split_path=args.splits_path,
                split_num=args.split_num),
                batch_size=args.dis_batch_size, shuffle=False,
                num_workers=args.num_workers, pin_memory=True, sampler=val_sampler)

            self.test = torch.utils.data.DataLoader(Splitter(
                val_dataset,
                split_path=args.splits_path,
                split_num=args.split_num),
                batch_size=args.dis_batch_size, shuffle=False,
                num_workers=args.num_workers, pin_memory=True, sampler=val_sampler)

        elif args.dataset.lower() == 'celeba':
            Dt = CelebA
            transform = transforms.Compose([
                transforms.Resize(size=(img_size, img_size)),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
            ])

            train_dataset = Dt(root=args.data_path, transform=transform)
            val_dataset = Dt(root=args.data_path, transform=transform)

            train_sampler = torch.utils.data.distributed.DistributedSampler(train_dataset)
            val_sampler = torch.utils.data.distributed.DistributedSampler(val_dataset)
            self.train_sampler = train_sampler
            self.train = torch.utils.data.DataLoader(
                train_dataset,
                batch_size=args.dis_batch_size, shuffle=(train_sampler is None),
                num_workers=args.num_workers, pin_memory=True, drop_last=True, sampler=train_sampler)

            self.valid = torch.utils.data.DataLoader(
                val_dataset,
                batch_size=args.dis_batch_size, shuffle=False,
                num_workers=args.num_workers, pin_memory=True, sampler=val_sampler)

            self.test = torch.utils.data.DataLoader(
                val_dataset,
                batch_size=args.dis_batch_size, shuffle=False,
                num_workers=args.num_workers, pin_memory=True, sampler=val_sampler)
        elif args.dataset.lower() == 'ffhq':
            Dt = FFHQ
            transform = transforms.Compose([
                transforms.Resize(size=(img_size, img_size)),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
            ])

            train_dataset = Dt(root=args.data_path, transform=transform)
            val_dataset = Dt(root=args.data_path, transform=transform)

            train_sampler = torch.utils.data.distributed.DistributedSampler(train_dataset)
            val_sampler = torch.utils.data.distributed.DistributedSampler(val_dataset)
            self.train_sampler = train_sampler

            self.train = torch.utils.data.DataLoader(
                train_dataset,
                batch_size=args.dis_batch_size, shuffle=(train_sampler is None),
                num_workers=args.num_workers, pin_memory=True, drop_last=True, sampler=train_sampler)

            self.valid = torch.utils.data.DataLoader(
                val_dataset,
                batch_size=args.dis_batch_size, shuffle=False,
                num_workers=args.num_workers, pin_memory=True, sampler=val_sampler)

            self.test = torch.utils.data.DataLoader(
                val_dataset,
                batch_size=args.dis_batch_size, shuffle=False,
                num_workers=args.num_workers, pin_memory=True, sampler=val_sampler)
        elif args.dataset.lower() == 'bedroom':
            Dt = datasets.LSUN
            transform = transforms.Compose([
                transforms.Resize(size=(img_size, img_size)),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
            ])

            train_dataset = Dt(root=args.data_path, classes=["bedroom_train"], transform=transform)
            val_dataset = Dt(root=args.data_path, classes=["bedroom_val"], transform=transform)

            train_sampler = torch.utils.data.distributed.DistributedSampler(train_dataset)
            val_sampler = torch.utils.data.distributed.DistributedSampler(val_dataset)
            self.train_sampler = train_sampler
            self.train = torch.utils.data.DataLoader(
                train_dataset,
                batch_size=args.dis_batch_size, shuffle=(train_sampler is None),
                num_workers=args.num_workers, pin_memory=True, drop_last=True, sampler=train_sampler)

            self.valid = torch.utils.data.DataLoader(
                val_dataset,
                batch_size=args.dis_batch_size, shuffle=False,
                num_workers=args.num_workers, pin_memory=True, sampler=val_sampler)

            self.test = torch.utils.data.DataLoader(
                val_dataset,
                batch_size=args.dis_batch_size, shuffle=False,
                num_workers=args.num_workers, pin_memory=True, sampler=val_sampler)
        elif args.dataset.lower() == 'church':
            Dt = datasets.LSUN
            transform = transforms.Compose([
                transforms.Resize(size=(img_size, img_size)),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
            ])

            train_dataset = Dt(root=args.data_path, classes=["church_outdoor_train"], transform=transform)
            val_dataset = Dt(root=args.data_path, classes=["church_outdoor_val"], transform=transform)

            train_sampler = torch.utils.data.distributed.DistributedSampler(train_dataset)
            val_sampler = torch.utils.data.distributed.DistributedSampler(val_dataset)
            self.train_sampler = train_sampler
            self.train = torch.utils.data.DataLoader(
                train_dataset,
                batch_size=args.dis_batch_size, shuffle=(train_sampler is None),
                num_workers=args.num_workers, pin_memory=True, drop_last=True, sampler=train_sampler)

            self.valid = torch.utils.data.DataLoader(
                val_dataset,
                batch_size=args.dis_batch_size, shuffle=False,
                num_workers=args.num_workers, pin_memory=True, sampler=val_sampler)

            self.test = torch.utils.data.DataLoader(
                val_dataset,
                batch_size=args.dis_batch_size, shuffle=False,
                num_workers=args.num_workers, pin_memory=True, sampler=val_sampler)
        else:
            raise NotImplementedError('Unknown dataset: {}'.format(args.dataset))
