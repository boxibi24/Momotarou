import dearpygui.dearpygui as dpg


class Link:
    def __init__(self,
                 source_node_tag,
                 source_node_instance,
                 source_pin_instance,
                 source_pin_type,
                 destination_node_tag,
                 destination_node_instance,
                 destination_pin_instance,
                 destination_pin_type,
                 parent
                 ):
        self._source_node_tag = source_node_tag
        self._source_node_instance = source_node_instance
        self._source_pin_instance = source_pin_instance
        self._source_pin_type = source_pin_type
        self._destination_node_tag = destination_node_tag
        self._destination_node_instance = destination_node_instance
        self._destination_pin_instance = destination_pin_instance
        self._destination_pin_type = destination_pin_type
        # Initialize dpg link
        self._link_id = dpg.add_node_link(source_pin_instance.pin_tag, destination_pin_instance.pin_tag, parent=parent)

    @property
    def link_id(self) -> int:
        return self._link_id

    @property
    def source_node_tag(self) -> str:
        return self._source_node_tag

    @property
    def source_node_instance(self):
        return self._source_node_instance

    @property
    def source_pin_instance(self) -> str:
        return self._source_pin_instance

    @property
    def source_pin_type(self) -> str:
        return self._source_pin_type

    @property
    def destination_node_tag(self) -> str:
        return self._destination_node_tag

    @property
    def destination_node_instance(self):
        return self._destination_node_instance

    @property
    def destination_pin_instance(self) -> str:
        return self._destination_pin_instance

    @property
    def destination_pin_type(self) -> str:
        return self._destination_pin_type

    @property
    def link_list(self) -> list[dict[str, str]]:
        return [
            {
                'id': self.source_pin_instance.pin_tag,
                'node': self.source_node_tag,
                'pin_type': self.source_pin_type,
            },
            {
                'id': self.destination_pin_instance.pin_tag,
                'node': self.destination_node_tag,
                'pin_type': self.destination_pin_type
            }
        ]
