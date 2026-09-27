# Clairmeta - (C) YMAGIS S.A.
# See LICENSE for more information

from clairmeta.dcp_check import CheckerBase
from clairmeta.dcp_utils import list_cpl_assets
from clairmeta.settings import DCP_SETTINGS


class Checker(CheckerBase):
    def __init__(self, dcp):
        super().__init__(dcp)

    def run_checks(self):
        for source in self.dcp._list_cpl:
            asset_checks = self.find_check("sound_cpl")
            [
                self.run_check(
                    check,
                    source,
                    asset,
                    stack=[source["FileName"], asset[1].get("Path") or asset[1]["Id"]],
                )
                for asset in list_cpl_assets(
                    source, filters="Sound", required_keys=["Probe"]
                )
                for check in asset_checks
            ]

        return self.checks

    def check_sound_cpl_channels(self, playlist, asset):
        """Sound max channels count.

        References:
            SMPTE ST 428-2:2006 3.3
        """
        channels = DCP_SETTINGS["sound"]["max_channel_count"]
        _, asset = asset
        cc = asset["Probe"]["ChannelCount"]

        if cc > channels:
            self.error(
                f"Invalid Sound ChannelCount, should be less than {channels} but got {cc}"
            )

    def check_sound_cpl_channels_odd(self, playlist, asset):
        """Sound channels count must be an even number.

        Extract fom ISDCF recommandation : Note 1. Not all channels need to
        be present in a given DCP. For instance, only the first 8 channels
        should be used when delivering 5.1 + HI/VI content. In all cases,
        an even number of channels shall be used.

        References:
            ISDCF Doc 04
            https://isdcf.com/papers/ISDCF-Doc4-Audio-channel-recommendations.pdf
        """
        _, asset = asset
        cc = asset["Probe"]["ChannelCount"]

        if cc % 2 != 0:
            self.error(
                f"Invalid Sound ChannelCount, should be an even number, got {cc}"
            )

    def check_sound_cpl_channel_assignments(self, playlist, asset):
        """Sound channel configuration shall be Wild Track (4).

        References:
            ISDCF Doc 04
            SMPTE RDD 52:2020 10.3.1
            SMPTE ST 429-2:2013 A.1.2
        """
        configurations = DCP_SETTINGS["sound"]["configuration_channels"]
        _, asset = asset
        cf = asset["Probe"]["ChannelFormat"]

        if cf in configurations and cf != 4:
            self.error(
                f'Detected channel assignments "{configurations[cf][0]}", but expected "{configurations[4][0]}"'
            )

    def check_sound_cpl_format(self, playlist, asset):
        """Sound channels count coherence with format.

        References:
            SMPTE ST 429-2:2013 A.1.2
        """
        configurations = DCP_SETTINGS["sound"]["configuration_channels"]
        _, asset = asset
        cf = asset["Probe"]["ChannelFormat"]
        cc = asset["Probe"]["ChannelCount"]

        if cf in configurations:
            label, min_cc, max_cc = configurations[cf]
            if label and cc < min_cc or cc > max_cc:
                self.error(
                    f"Invalid Sound ChannelCount, {label} require between {min_cc} and {max_cc} "
                    f"channels, got {cc}"
                )

    def check_sound_cpl_sampling(self, playlist, asset):
        """Sound sampling rate check.

        References:
            SMPTE ST 428-2:2006 3.2
        """
        rates = DCP_SETTINGS["sound"]["sampling_rate"]
        _, asset = asset
        sr = asset["Probe"]["AudioSamplingRate"]

        if sr not in rates:
            self.error(
                f"Invalid Sound SamplingRate, expected {rates} but got {sr}"
            )

    def check_sound_cpl_quantization(self, playlist, asset):
        """Sound quantization check.

        References:
            SMPTE ST 428-2:2006 3.1
        """
        bitdepth = DCP_SETTINGS["sound"]["quantization"]
        _, asset = asset
        depth = asset["Probe"]["QuantizationBits"]

        if depth != bitdepth:
            self.error(
                f"Invalid Sound Quantization, expected {bitdepth} but got {depth}"
            )

    def check_sound_cpl_blockalign(self, playlist, asset):
        """Sound block alignement check.

        References: N/A
        """
        align = DCP_SETTINGS["sound"]["quantization"] / 8
        _, asset = asset
        al = asset["Probe"]["BlockAlign"]
        cc = asset["Probe"]["ChannelCount"]

        if al != cc * align:
            self.error(
                f"Invalid Sound BlockAlign, expected {cc * align} but got {al} (it should "
                "be ChannelCount x 3)"
            )
