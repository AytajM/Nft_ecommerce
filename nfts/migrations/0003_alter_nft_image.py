# Generated by Django 4.2.3 on 2023-07-28 12:12

from django.db import migrations, models
import nfts.models


class Migration(migrations.Migration):

    dependencies = [
        ('nfts', '0002_nft_artist_nft_auction_end_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nft',
            name='image',
            field=models.ImageField(upload_to=nfts.models.upload_nfts),
        ),
    ]
