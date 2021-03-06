import torch
import transformers
from torch import nn


class ModelInterface:
    """Binary classification model
     interface for review 'intent' classification"""

    def __init__(self, model_bin, device, tokenizer_state):
        """Uses base BETO model"""
        self.model = ReviewClassifier(
            n_classes=4,
            pre_trained_model='dccuchile/bert-base-spanish-wwm-cased'
        )
        self.model_bin = model_bin
        self.device = device
        self.tokenizer = transformers.BertTokenizer\
            .from_pretrained(tokenizer_state)
        self.classes = ['Other', 'Service', 'App', 'App and Service']

    def model_ramp_up(self):
        """This loads the model to the cpu or the device. Takes time"""
        self.model.load_state_dict(
            torch.load(
                self.model_bin,
                map_location=torch.device(self.device)
            )
        )

    def __str__(self):
        # TODO: Print all necessesary things
        print(f'Mounted on: {self.device}')
        print('Model architecture:')
        print(self.model)

    def predict(self, txt):
        self.model.eval()
        encoded_review = self.tokenizer.encode_plus(
            txt,
            max_length=70,
            add_special_tokens=True,
            return_token_type_ids=False,
            padding='max_length',
            return_attention_mask=True,
            return_tensors='pt'
        )
        input_ids = encoded_review['input_ids'].to(torch.device(self.device))
        attention_mask = encoded_review['attention_mask'] \
            .to(torch.device(self.device))

        output = self.model(input_ids, attention_mask)
        _, prediction = torch.max(output, dim=1)
        return {
            'input': txt,
            'prediction': self.classes[prediction],
            'prediction values': {
                'other': output.tolist()[0][0],
                'service': output.tolist()[0][1],
                'app': output.tolist()[0][2],
                'app and service': output.tolist()[0][3]
            }
        }


class ReviewClassifier(nn.Module):

    def __init__(self, n_classes, pre_trained_model):
        super(ReviewClassifier, self).__init__()
        self.bert = transformers.BertModel.from_pretrained(pre_trained_model)
        self.drop = nn.Dropout(p=0.3)
        self.out = nn.Linear(self.bert.config.hidden_size, n_classes)

    def forward(self, input_ids, attention_mask):
        _, pooled_output = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        output = self.drop(pooled_output)
        return self.out(output)
