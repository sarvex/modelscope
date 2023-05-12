from dataclasses import dataclass, field

from modelscope.metainfo import Trainers
from modelscope.msdatasets import MsDataset
from modelscope.trainers import build_trainer
from modelscope.trainers.training_args import (TrainingArgs, get_flatten_value,
                                               set_flatten_value)


@dataclass
class TokenClassificationArguments(TrainingArgs):

    trainer: str = field(
        default=Trainers.default, metadata={
            'help': 'The trainer used',
        })

    preprocessor: str = field(
        default=None,
        metadata={
            'help': 'The preprocessor type',
            'cfg_node': 'preprocessor.type'
        })

    preprocessor_padding: str = field(
        default=None,
        metadata={
            'help': 'The preprocessor padding',
            'cfg_node': 'preprocessor.padding'
        })

    train_dataset_params: str = field(
        default=None,
        metadata={
            'cfg_node': 'dataset.train',
            'cfg_getter': get_flatten_value,
            'cfg_setter': set_flatten_value,
            'help': 'The parameters for train dataset',
        })

    def __call__(self, config):
        config = super().__call__(config)
        if config.safe_get('dataset.train.label') == 'ner_tags':
            ner_tags_labels = train_dataset['ner_tags'] + eval_dataset[
                'ner_tags']
            label_enumerate_values = self._get_label_list(ner_tags_labels)
            config.merge_from_dict(
                {'dataset.train.labels': label_enumerate_values})
        if config.train.lr_scheduler.type == 'LinearLR':
            config.train.lr_scheduler['total_iters'] = \
                int(len(train_dataset) / self.per_device_train_batch_size) * self.max_epochs
        return config

    # TODO: Future performance optimization in MsDataset
    @staticmethod
    def _get_label_list(labels):
        unique_labels = set()
        for label in labels:
            unique_labels = unique_labels | set(label)
        return sorted(unique_labels)


args = TokenClassificationArguments.from_cli(task='token-classification')
print(args)

# load dataset
train_dataset = MsDataset.load(
    args.dataset_name,
    subset_name=args.subset_name,
    split='train',
    namespace='damo')['train']
eval_dataset = MsDataset.load(
    args.dataset_name,
    subset_name=args.subset_name,
    split='validation',
    namespace='damo')['validation']

kwargs = dict(
    model=args.model,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    work_dir=args.work_dir,
    cfg_modify_fn=args)

trainer = build_trainer(name=args.trainer, default_args=kwargs)
trainer.train()
