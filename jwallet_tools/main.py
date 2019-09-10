from jwallet_tools.validation_service.classes import KafkaAssetValidator


def validate_fn():
    obj = KafkaAssetValidator()
    obj.process_message()


validate_fn()

