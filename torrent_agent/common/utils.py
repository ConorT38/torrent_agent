from torrent_agent.common.configuration import Configuration

configuration  = Configuration()
def file_name_to_cdn_path(file_name: str) -> str:
    """
    Convert a file_name to a cdn_path based on the media root from Configuration.get_media().
    
    Args:
        file_name (str): The full file path.
        
    Returns:
        str: The CDN path.
    """
    media_root = configuration.get_media_directory()
    if file_name.startswith(media_root):
        return file_name[len(media_root):]
    else:
        raise ValueError(f"File name '{file_name}' does not start with media root '{media_root}'")