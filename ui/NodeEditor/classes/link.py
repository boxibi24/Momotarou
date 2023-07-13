import dearpygui.dearpygui as dpg


class Link:
    def __init__(self,
                 source_node_tag,
                 source_node_instance,
                 source_pin_instance,
                 source_pin_type,
                 target_node_tag,
                 target_node_instance,
                 target_pin_instance,
                 target_pin_type,
                 parent
                 ):
        self._source_node_tag = source_node_tag
        self._source_node_instance = source_node_instance
        self._source_pin_instance = source_pin_instance
        self._source_pin_type = source_pin_type
        self._target_node_tag = target_node_tag
        self._target_node_instance = target_node_instance
        self._target_pin_instance = target_pin_instance
        self._target_pin_type = target_pin_type
        # Initialize dpg link
        self._link_id = dpg.add_node_link(source_pin_instance.pin_tag, target_pin_instance.pin_tag, parent=parent)

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
    def target_node_tag(self) -> str:
        return self._target_node_tag

    @property
    def target_node_instance(self):
        return self._target_node_instance

    @property
    def target_pin_instance(self) -> str:
        return self._target_pin_instance

    @property
    def target_pin_type(self) -> str:
        return self._target_pin_type

    @property
    def link_list(self) -> list[dict[str, str]]:
        return [
            {
                'id': self.source_pin_instance.pin_tag,
                'node': self.source_node_tag,
                'pin_type': self.source_pin_type,
            },
            {
                'id': self.target_pin_instance.pin_tag,
                'node': self.target_node_tag,
                'pin_type': self.target_pin_type
            }
        ]
