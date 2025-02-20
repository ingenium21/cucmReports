"""CUCM Media Configuration APIs."""

from .._internal_utils import flatten_signature_kwargs
from .base import DeviceAXLAPI
from .base import SimpleAXLAPI


class Announcement(SimpleAXLAPI):
    _factory_descriptor = "announcement"

    def add(self, name,
            announcementFile=None,
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class Annunciator(SimpleAXLAPI):
    _factory_descriptor = "annunciator"
    supported_methods = ["get", "list", "update", "model"]


class ConferenceBridge(DeviceAXLAPI):
    _factory_descriptor = "conference_bridge"

    def add(self, name, devicePoolName, product="Cisco IOS Conference Bridge", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class FixedMohAudioSource(SimpleAXLAPI):
    _factory_descriptor = "fixed_moh_audio_source"
    supported_methods = ['update', 'get']


class MediaResourceGroup(SimpleAXLAPI):
    _factory_descriptor = "mrg"

    def add(self, name, members, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class MediaResourceList(SimpleAXLAPI):
    _factory_descriptor = "mrgl"

    def add(self, name, members, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


# experimental - not tested
class MobileVoiceAccess(SimpleAXLAPI):
    _factory_descriptor = "mobile_voice_access"
    supported_methods = ['add', 'get', 'update', 'remove', 'add_update']

    def add(self, pattern, locales, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class MohAudioSource(SimpleAXLAPI):
    _factory_descriptor = "moh_audio_source"
    supported_methods = ['get', 'update', 'list', 'remove']

    
class MohServer(SimpleAXLAPI):
    _factory_descriptor = "moh_server"
    supported_methods = ["get", "list", "update", "model"]


class Mtp(DeviceAXLAPI):
    _factory_descriptor = "mtp"

    def add(self, name, devicePoolName, mtpType="Cisco IOS Enhanced Software Media Termination Point", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class Transcoder(DeviceAXLAPI):
    _factory_descriptor = "transcoder"
    supported_methods = ["model", "create", "add", "get", "list", "update", "remove", "apply", "reset", "add_update"]

    def add(self, name, devicePoolName, product="Cisco IOS Enhanced Media Termination Point",
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class VohServer(SimpleAXLAPI):
    _factory_descriptor = "voh_server"

    def add(self, name, sipTrunkName, defaultVideoStreamId="SampleVideo", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)
