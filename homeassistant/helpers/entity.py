"""
homeassistant.helpers.entity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides ABC for entities in HA.
"""

from collections import defaultdict

from homeassistant import NoEntitySpecifiedError

from homeassistant.const import (
    ATTR_FRIENDLY_NAME, ATTR_UNIT_OF_MEASUREMENT, ATTR_HIDDEN,
    ATTR_ENTITY_PICTURE, STATE_ON, STATE_OFF, DEVICE_DEFAULT_NAME,
    TEMP_CELCIUS, TEMP_FAHRENHEIT)

# Dict mapping entity_id to a boolean that overwrites the hidden property
_OVERWRITE = defaultdict(dict)


class Entity(object):
    """ ABC for Home Assistant entities. """
    # pylint: disable=no-self-use

    _hidden = False

    # SAFE TO OVERWRITE
    # The properties and methods here are safe to overwrite when inherting this
    # class. These may be used to customize the behavior of the entity.

    @property
    def should_poll(self):
        """
        Return True if entity has to be polled for state.
        False if entity pushes its state to HA.
        """
        return True

    @property
    def unique_id(self):
        """ Returns a unique id. """
        return "{}.{}".format(self.__class__, id(self))

    @property
    def name(self):
        """ Returns the name of the entity. """
        return self.get_name()

    @property
    def state(self):
        """ Returns the state of the entity. """
        return self.get_state()

    @property
    def state_attributes(self):
        """ Returns the state attributes. """
        return {}

    @property
    def unit_of_measurement(self):
        """ Unit of measurement of this entity, if any. """
        return None

    @property
    def hidden(self):
        """ Suggestion if the entity should be hidden from UIs. """
        return self._hidden

    @hidden.setter
    def hidden(self, val):
        """ Sets the suggestion for visibility. """
        self._hidden = bool(val)

    def update(self):
        """ Retrieve latest state. """
        pass

    # DEPRECATION NOTICE:
    # Device is moving from getters to properties.
    # For now the new properties will call the old functions
    # This will be removed in the future.

    def get_name(self):
        """ Returns the name of the entity if any. """
        return DEVICE_DEFAULT_NAME

    def get_state(self):
        """ Returns state of the entity. """
        return "Unknown"

    def get_state_attributes(self):
        """ Returns optional state attributes. """
        return None

    # DO NOT OVERWRITE
    # These properties and methods are either managed by Home Assistant or they
    # are used to perform a very specific function. Overwriting these may
    # produce undesirable effects in the entity's operation.

    hass = None
    entity_id = None

    def update_ha_state(self, force_refresh=False):
        """
        Updates Home Assistant with current state of entity.
        If force_refresh == True will update entity before setting state.
        """
        if self.hass is None:
            raise RuntimeError("Attribute hass is None for {}".format(self))

        if self.entity_id is None:
            raise NoEntitySpecifiedError(
                "No entity id specified for entity {}".format(self.name))

        if force_refresh:
            self.update()

        state = str(self.state)
        attr = self.state_attributes or {}

        if ATTR_FRIENDLY_NAME not in attr and self.name:
            attr[ATTR_FRIENDLY_NAME] = self.name

        if ATTR_UNIT_OF_MEASUREMENT not in attr and self.unit_of_measurement:
            attr[ATTR_UNIT_OF_MEASUREMENT] = self.unit_of_measurement

        if _OVERWRITE[ATTR_HIDDEN].get(self.entity_id, self.hidden):
            attr[ATTR_HIDDEN] = True

        if _OVERWRITE[ATTR_ENTITY_PICTURE].get(self.entity_id, False):
            attr[ATTR_ENTITY_PICTURE] = \
                _OVERWRITE[ATTR_ENTITY_PICTURE][self.entity_id]

        # Convert temperature if we detect one
        if attr.get(ATTR_UNIT_OF_MEASUREMENT) in (TEMP_CELCIUS,
                                                  TEMP_FAHRENHEIT):

            state, attr[ATTR_UNIT_OF_MEASUREMENT] = \
                self.hass.config.temperature(
                    state, attr[ATTR_UNIT_OF_MEASUREMENT])
            state = str(state)

        return self.hass.states.set(self.entity_id, state, attr)

    def __eq__(self, other):
        return (isinstance(other, Entity) and
                other.unique_id == self.unique_id)

    def __repr__(self):
        return "<Entity {}: {}>".format(self.name, self.state)

    @staticmethod
    def overwrite_attribute(entity_id, attr, val):
        """
        Overwrite the hidden property of an entity.
        Set hidden to None to remove any overwritten value in place.
        """
        if val is None:
            _OVERWRITE[attr].pop(entity_id, None)
        else:
            _OVERWRITE[attr][entity_id.lower()] = val


class ToggleEntity(Entity):
    """ ABC for entities that can be turned on and off. """
    # pylint: disable=no-self-use

    @property
    def state(self):
        """ Returns the state. """
        return STATE_ON if self.is_on else STATE_OFF

    @property
    def is_on(self):
        """ True if entity is on. """
        return False

    def turn_on(self, **kwargs):
        """ Turn the entity on. """
        pass

    def turn_off(self, **kwargs):
        """ Turn the entity off. """
        pass
