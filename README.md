# Home Assistant integration for [CamillaDSP](https://github.com/HEnquist/camilladsp)

This is a Home Assistant custom integration, that adds a media player entity to control CamillaDSP.

## Supported Features

- Get state (Playing, Paused, Idle,...)
- Get and set volume level
- Get and set mute state
- Get and set active file
- Get capture rate

## Installation

### HACS

- Install HACS
- Goto "HACS / Integrations"
- Click on the three dots in the top right corner
- Click on "Custom Repositories"
- Add:
  - Repository: "kwerner72/homeassistant-camilladsp"
  - Category: "Integration"
- Search for "CamillaDSP" in the repositories
- Click on "CamillaDSP"
- Click on "Download" button in the bottom right corner
- Restart Home Assistant

### manual

- copy folder `camilladsp` in `custom_components` to your home assistant folder `config/custom_components`
- restart Home Assistant

## Setup

- Goto "Settings / Devices & services"
- Click on "Add integration"
- Search for "CamillaDSP"
- Enter the URL of your CamillaDSP instance (eg. 'http://localhost:5005')
- Select the Area your CamillaDSP is running in

## Configuration

The integration can be configured with its "Configure" button
In the dialog, three values can be configured:

1. Volume min: lower volume limit (in dB)
2. Volume max: upper volume limit (in dB)
3. Volume step: volume increase/decrease amount (in dB)

## Usage

The CamillaDSP entity provides some media player functionality to control CamillaDSP and get status information.

### Supported Attributes

- source_list: list of available config files
- volume_level: current volume level (0..1)
- is_volume_muted: current mute state
- source: currently active config file
- volume_db: current volume level (in dB)
- capturerate: current capture rate

### Supported services

#### media_player.select_source
Sets the active config file.  
"data.source" must contain the filename.

Example:

```yaml
type: button
entity: media_player.camilladsp_01234
tap_action:
  action: perform-action
  perform_action: media_player.select_source
  target:
    entity_id: media_player.camilladsp_01234
  data:
    source: default.yml
```

#### media_player.volume_up / media_player.volume_down

Increases / decreases current volume level.

Example:

```yaml
type: button
entity: media_player.camilladsp_01234
tap_action:
  action: perform-action
  perform_action: media_player.volume_down
  target:
    entity_id: media_player.camilladsp_01234
icon: mdi:volume-minus
```

#### media_player.volume_mute

Mutes / unmutes volume.  
"data.is_volume_muted" must be either "true" or "false".

Example:

```yaml
type: button
entity: media_player.camilladsp_01234
tap_action:
  action: perform-action
  perform_action: media_player.volume_mute
  target:
    entity_id: media_player.camilladsp_01234
  data:
    is_volume_muted: true
icon: mdi:volume-mute
```

#### media_player.volume_set

Sets the volume to a certain level.  
"data.volume_level" must be within 0 and 1.

Example:

```yaml
type: button
entity: media_player.camilladsp_01234
tap_action:
  action: perform-action
  perform_action: media_player.volume_set
  target:
    entity_id: media_player.camilladsp_01234
  data:
    volume_level: 0.8
```

#### camilladsp.volume_set_db

Sets the volume to a certain level.  
"data.volume_level_db" must be <= 0.

Example:

```yaml
type: button
entity: media_player.camilladsp_01234
tap_action:
  action: perform-action
  perform_action: camilladsp.volume_set_db
  target:
    entity_id: media_player.camilladsp_01234
  data:
    volume_level_db: -20
```

### Status mappings

States from CamillaDSP will be mapped to Home Assistant states.

| CamillaDSP    | Home Assistant |
| ------------- | -------------- |
| INACTIVE      | STANDBY        |
| PAUSED        | PAUSED         |
| RUNNING       | PLAYING        |
| STALLED       | IDLE           |
| STARTING      | ON             |
| not available | OFF            |